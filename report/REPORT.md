# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Trần Ngọc Hùng
**Nhóm:** [Hung-Thang]
**Bao gồm:**
- Trần Ngọc Hùng - 2A202600429
- Bùi Đức Thắng - 2A202600002
**Ngày:** 10/04/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> High cosine similarity nghĩa là hai đoạn text có vector embedding gần cùng hướng trong không gian biểu diễn, nên nội dung hoặc chủ đề của chúng tương đối giống nhau. Điểm càng cao thì mức độ tương đồng ngữ nghĩa càng lớn.

**Ví dụ HIGH similarity:**
- Sentence A: The cat sat on the mat.
- Sentence B: A kitten rested on the rug.
- Tại sao tương đồng: Cả hai câu đều nói về một con mèo đang nằm hoặc nghỉ trên một bề mặt, nên ý nghĩa tổng thể khá gần nhau.

**Ví dụ LOW similarity:**
- Sentence A: The cat sat on the mat.
- Sentence B: Stock prices rose sharply today.
- Tại sao khác: Một câu nói về động vật, câu còn lại nói về thị trường tài chính nên chủ đề gần như không liên quan.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Cosine similarity đo góc giữa hai vector nên tập trung vào hướng nghĩa thay vì độ lớn tuyệt đối của vector. Với text embeddings, điều này hữu ích hơn Euclidean distance vì độ dài câu hoặc cách mã hóa có thể làm thay đổi magnitude nhưng không nhất thiết làm thay đổi ý nghĩa.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Trình bày phép tính: `ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11)`
> Đáp án: `23 chunks`

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> Khi overlap tăng lên 100 thì số chunk trở thành `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = 25`. Overlap lớn hơn làm tăng số chunk nhưng giúp giữ thêm ngữ cảnh giữa các chunk liền kề, giảm nguy cơ cắt mất ý quan trọng ở ranh giới.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Platform governance and online service policies

**Tại sao nhóm chọn domain này?**
> Nhóm chọn bộ tài liệu chính sách của GitHub vì đây là nguồn chính thức, nội dung dài và có cấu trúc rõ ràng theo mục, rất phù hợp để thử các chiến lược chunking khác nhau. Ngoài ra, 5 tài liệu này bao phủ nhiều khía cạnh khác nhau như điều khoản sử dụng, quyền riêng tư, nội dung bị cấm, gỡ bỏ bản quyền, và yêu cầu từ chính phủ, nên rất thuận lợi để thiết kế benchmark queries đa dạng.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | GitHub Terms of Service | GitHub Docs, https://docs.github.com/en/site-policy/github-terms/github-terms-of-service | ≈ 33,000 | `policy_type=terms`, `source=github`, `language=en` |
| 2 | GitHub General Privacy Statement | GitHub Docs, https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement | ≈ 22,000 | `policy_type=privacy`, `source=github`, `language=en` |
| 3 | GitHub Acceptable Use Policies | GitHub Docs, https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies | ≈ 16,000 | `policy_type=acceptable_use`, `source=github`, `language=en` |
| 4 | DMCA Takedown Policy | GitHub Docs, https://docs.github.com/en/site-policy/content-removal-policies/dmca-takedown-policy | ≈ 28,000 | `policy_type=copyright`, `source=github`, `language=en` |
| 5 | GitHub Government Takedown Policy | GitHub Docs, https://docs.github.com/en/site-policy/other-site-policies/github-government-takedown-policy | ≈ 7,000 | `policy_type=government_request`, `source=github`, `language=en` |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| `policy_type` | string | `privacy`, `terms`, `acceptable_use` | Giúp filter đúng nhóm tài liệu khi query hỏi về một loại chính sách cụ thể. |
| `source` | string | `github` | Hữu ích nếu sau này mở rộng corpus với nhiều tổ chức hoặc nhiều website chính sách khác nhau. |
| `language` | string | `en` | Cho phép lọc theo ngôn ngữ nếu benchmark có cả tài liệu tiếng Anh và tiếng Việt. |
| `topic_scope` | string | `copyright`, `user_data`, `account_rules` | Giúp retrieval chính xác hơn khi câu hỏi tập trung vào một chủ đề hẹp trong policy corpus. |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| GitHub Terms of Service | FixedSizeChunker (`fixed_size`) | 70 | 795.6 | Context giữ ở mức trung bình; các đoạn chính sách dài có thể bị cắt giữa ý. |
| DMCA Takedown Policy | FixedSizeChunker (`fixed_size`) | 31 | 787.4 | Dễ retrieve theo từ khóa, nhưng các bước quy trình DMCA có lúc bị chia sang chunk kế tiếp. |
| GitHub Government Takedown Policy | FixedSizeChunker (`fixed_size`) | 5 | 734.4 | Tài liệu ngắn nên chunk tương đối mạch lạc và ít bị mất ngữ cảnh hơn. |

### Strategy Của Tôi

**Loại:** FixedSizeChunker

**Mô tả cách hoạt động:**
> Tôi chọn `FixedSizeChunker` với `chunk_size=800` và `overlap=120`. Strategy này chia tài liệu thành các khối có độ dài gần như đồng đều, đồng thời giữ một phần nội dung chồng lấn giữa hai chunk liên tiếp để giảm rủi ro mất ngữ cảnh ở ranh giới. Với tài liệu policy dài, cách chia này giúp retrieval ổn định và rất dễ kiểm soát số lượng chunk.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Tôi chọn strategy này vì bộ GitHub policy có độ dài lớn, nhiều mục con, và rất nhiều cụm từ pháp lý lặp lại. Fixed-size chunking tạo ra các đoạn khá đều nhau, nên mô hình embedding dễ so sánh hơn và tôi cũng dễ benchmark giữa các tài liệu. Điểm đổi lại là đôi khi một quy tắc quan trọng bị tách giữa hai chunk liền kề.

**Code snippet (nếu custom):**
```python
chunker = FixedSizeChunker(chunk_size=800, overlap=120)
chunks = chunker.chunk(text)
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| GitHub policy corpus | best baseline hiện có | 5/5 top-1, 5/5 top-3 | khoảng 734-796 ký tự/chunk | Retrieval theo từ khóa rất tốt, đặc biệt ở các query có policy_type rõ ràng. |
| GitHub policy corpus | **của tôi** (`FixedSizeChunker`) | 70 / 31 / 5 trên 3 tài liệu mẫu | 795.6 / 787.4 / 734.4 | Chạy ổn định, score cao, nhưng có hiện tượng cắt giữa ý ở các policy section dài. |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Điểm mạnh | Điểm yếu |
|-----------|----------|-----------|----------|
| Trần Ngọc Hùng | FixedSizeChunker | Top-1 và top-3 đều đúng ở cả 5 benchmark queries; dễ benchmark và ổn định | Có thể cắt section quan trọng giữa hai chunk liên tiếp |
|Trần Ngọc Hùng| SentenceChunker | Chunk dễ đọc, bám theo câu nên thuận lợi cho giải thích kết quả | Một số policy sentence quá dài, làm chunk vượt kích thước mong muốn và có thể gây lỗi embedding hoặc giảm tính ổn định |
|Bùi Đức Thắng| RecursiveChunker | Giữ cấu trúc heading, paragraph, và section tốt hơn; tiềm năng grounding cao | Kích thước chunk không đều và vẫn cần kiểm soát thêm để tránh chunk quá dài ở một số section pháp lý |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> Với benchmark cá nhân hiện tại, `FixedSizeChunker` cho kết quả retrieval rất mạnh vì đạt 5/5 top-1 hit và 5/5 top-3 hit. Tuy nhiên, nếu nhóm ưu tiên chunk mạch lạc hơn để giải thích kết quả và grounding tốt hơn, một strategy như `RecursiveChunker` vẫn có khả năng vượt lên trong so sánh cuối cùng.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Tôi dùng regex `(?<=[.!?])(?:\s+|\n)` để tách tại ranh giới câu sau dấu chấm, chấm than, hoặc chấm hỏi. Sau khi split, tôi `strip()` từng phần và bỏ chuỗi rỗng để tránh sinh chunk bẩn khi input có nhiều khoảng trắng hoặc xuống dòng liên tiếp. Cuối cùng, các câu được gom theo `max_sentences_per_chunk` và nối lại bằng một khoảng trắng.

**`RecursiveChunker.chunk` / `_split`** — approach:
> `chunk()` chỉ xử lý trường hợp input rỗng rồi gọi `_split()` và lọc bỏ phần tử trống. Trong `_split()`, base case là khi đoạn hiện tại đã nhỏ hơn hoặc bằng `chunk_size`, hoặc khi không còn separator nào để thử nữa. Nếu separator hiện tại là chuỗi rỗng thì tôi fallback sang cắt theo lát ký tự cố định; còn nếu không thì thuật toán gom dần các phần nhỏ thành chunk và đệ quy trên những phần riêng lẻ vẫn còn quá dài.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> Tôi chuẩn hóa mỗi document thành một record gồm `id`, `content`, `embedding`, và `metadata` rồi lưu vào `_store` trong bộ nhớ. Khi search, query được embed bằng cùng hàm embedding và so điểm bằng dot product với embedding của từng record. Kết quả sau đó được sort giảm dần theo `score` và cắt còn `top_k`.

**`search_with_filter` + `delete_document`** — approach:
> Với `search_with_filter`, tôi filter record theo metadata trước rồi mới tính similarity trên tập đã lọc để tránh chấm điểm cho tài liệu không liên quan về mặt thuộc tính. Với `delete_document`, tôi rebuild lại `_store` bằng list comprehension và bỏ toàn bộ record có `metadata["doc_id"]` trùng với document cần xóa. Hàm trả về `True` nếu kích thước store giảm xuống sau thao tác xóa.

### KnowledgeBaseAgent

**`answer`** — approach:
> Tôi implement theo pattern RAG cơ bản: retrieve top-k chunk liên quan trước, rồi ghép chúng thành một phần `Context`. Mỗi chunk được đánh số `[1]`, `[2]`, `[3]` để prompt rõ nguồn ngữ cảnh đang cung cấp cho LLM. Sau đó tôi thêm `Question` và `Answer:` để `llm_fn` có một prompt đơn giản nhưng đủ cấu trúc.

### Test Results

```
============================= test session starts ==============================
platform darwin -- Python 3.13.5, pytest-9.0.2, pluggy-1.5.0
cachedir: .pytest_cache
rootdir: /Users/hungcucu/Documents/assignments/Day07/2A202600429-TranNgocHung-Day07
plugins: langsmith-0.7.26, anyio-4.13.0
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

============================== 42 passed in 0.02s ==============================
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Python is a programming language | Java is a programming language | high | 0.1135 | Có |
| 2 | I love cats | I hate cats | high | 0.0829 | Có |
| 3 | Machine learning uses data | The weather is sunny today | low | -0.0529 | Có |
| 4 | Vector databases store embeddings | Embeddings are stored in vector DBs | high | 0.0236 | Không |
| 5 | Hello world | Xin chao the gioi | high | 0.0935 | Có |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Cặp làm tôi bất ngờ nhất là "Vector databases store embeddings" và "Embeddings are stored in vector DBs" vì về nghĩa chúng gần như tương đương nhưng điểm lại khá thấp với `_mock_embed`. Điều này cho thấy chất lượng reflection phụ thuộc mạnh vào embedding model: embedder giả lập hoặc đơn giản có thể không bắt được paraphrase tốt, nên kết quả similarity không phải lúc nào cũng phản ánh đúng trực giác ngữ nghĩa.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | Under what circumstances may GitHub access the contents of private repositories? | GitHub treats private repositories as confidential and may access them only in limited cases such as security, support, service integrity, legal compliance, suspected law violation, or user consent. |
| 2 | What kinds of behavior or content are prohibited under GitHub's Acceptable Use Policies? | Prohibited behavior includes abuse, privacy violations, spam, inauthentic activity, misuse of service data, and other harmful or unlawful conduct. |
| 3 | If content is removed by mistake under the DMCA process, what can the user do? | The user can submit a DMCA counter-notice to seek reinstatement when removal happened by mistake or misidentification. |
| 4 | What information must a government takedown request provide before GitHub acts on it? | The request must come from an official government agency, identify the illegal content, and specify the legal basis or source of illegality clearly enough for GitHub to review. |
| 5 | What privacy rights do users have over their personal data? | Users may request access, correction, deletion, objection, or restriction depending on region and applicable law. |

### Kết Quả Của Tôi

**Query 1:** Under what circumstances may GitHub access the contents of private repositories?  
**Top-1 Retrieved Chunk:** Chunk trong Terms of Service nói GitHub chỉ truy cập private repositories trong các trường hợp giới hạn và tham chiếu Privacy Statement.  
**Score:** `0.8049`  
**Relevant:** Yes  
**Agent Answer (actual):**
> GitHub will only look inside your private repositories in the narrow situations that the Privacy Statement (and the accompanying legal policy) specifically allows. In plain English, the only times GitHub personnel or systems can read the code, data, or any other content you keep private are:
>
> | Reason | What it covers |
> |--------|----------------|
> | **Security** | To detect and mitigate threats such as malware, phishing, or other malicious activity that might harm the GitHub platform or its users. |
> | **Automated / manual scanning** | For known security vulnerabilities, code quality checks, or content that is known to violate GitHub’s Terms of Service (e.g., illegal content, hate speech, etc.). |
> | **Support** | If you or a GitHub support rep request help with a technical issue in your repository. |
> | **Service integrity** | To keep the GitHub service running smoothly, which can involve investigating performance, reliability, or compliance issues. |
> | **Legal compliance** | If GitHub has a legal obligation (e.g., a court order or a lawful request) that the repository’s contents may be in violation of the law. |
> | **User-consented services** | When you explicitly enable a GitHub feature or third-party service that requires additional rights to your private content. GitHub will disclose those rights in the feature’s privacy explanation. |
>
> Outside of these scenarios, GitHub personnel do **not** access the contents of your private repositories without your explicit permission or a legal requirement.

**Query 2:** What kinds of behavior or content are prohibited under GitHub's Acceptable Use Policies?  
**Top-1 Retrieved Chunk:** Chunk trong Acceptable Use Policies liệt kê nội dung unlawful, safety abuse, privacy violation, spam, và impersonation.  
**Score:** `0.8046`  
**Relevant:** Yes  
**Agent Answer (actual):**
> **Under GitHub’s Acceptable Use Policies, the following types of behavior or content are prohibited:**
>
> | Category | Examples of Prohibited Content / Actions |
> |----------|-------------------------------------------|
> | **Intellectual-property violations** | Copyright, patent, trademark, or trade-secret infringement; unlawfully sharing or distributing product-licensing keys, key-generation tools, or software that bypasses licensing checks. |
> | **Impersonation / Identity fraud** | Pretending to be another person, entity, or GitHub employee; falsely claiming affiliation with GitHub or another organization. |
> | **Unlawful activity** | Content that is itself illegal or that promotes the planning or execution of illegal acts. |
> | **Sexually-obscene or exploitative content** | Depictions of sexual content that are obscene, exploit minors, or involve sexual abuse. |
> | **Defamation / false statements** | Libelous, fraudulent, or intentionally deceptive claims that could damage reputations or misinform. |
> | **Hate speech / discrimination** | Discriminatory or abusive language toward any individual or group. |
> | **Misinformation / disinformation** | False or inaccurate information that could adversely affect public interests such as health, safety, elections, or civic participation. |
> | **Harassment / abuse** | Harassing or abusive language toward other users. |
> | **Privacy violations** | Doxxing, posting personal information of third parties without consent, or otherwise violating privacy. |
> | **Spam and inauthentic activity** | Automated bulk actions or coordinated inauthentic behavior such as mass-spamming, unauthorized bulk promotion or advertising, and cryptocurrency mining scripts or other resource-exploiting code. |
>
> These rules are designed to keep GitHub a safe, reliable, and respectful platform for all users. Any content or activity that falls into one of the above categories is disallowed and may result in removal or account action.

**Query 3:** If content is removed by mistake under the DMCA process, what can the user do?  
**Top-1 Retrieved Chunk:** Chunk trong DMCA Takedown Policy nói người dùng có thể gửi counter-notice nếu nội dung bị gỡ do mistake hoặc misidentification.  
**Score:** `0.6912`  
**Relevant:** Yes  
**Agent Answer (actual):**
> If a takedown turns out to be a mistake, the user can file a **DMCA counter-notice**. In the counter-notice they must give enough detail as outlined in GitHub’s guide. Once submitted, GitHub will post the counter-notice to its public DMCA repository and forward it to the copyright owner. If the owner still wishes to keep the content disabled, they can pursue legal action.

**Query 4:** What information must a government takedown request provide before GitHub acts on it?  
**Top-1 Retrieved Chunk:** Chunk trong Government Takedown Policy mô tả request phải đến từ cơ quan chính thức, chỉ rõ nội dung bất hợp pháp và cơ sở pháp lý.  
**Score:** `0.7702`  
**Relevant:** Yes  
**Agent Answer (actual):**
> A government takedown request must be a **complete** request, which GitHub defines as including:
>
> 1. **The official request itself**: the government-issued notice or order that identifies the content to be removed.
> 2. **The geographic scope**: a clear specification of the jurisdiction that the takedown applies to, limited to the smallest area necessary.
> 3. **Public posting**: the official request must be posted in GitHub’s public `gov-takedowns` repository.
>
> Only when those elements are provided does GitHub act on the request.

**Query 5:** What privacy rights do users have over their personal data?  
**Top-1 Retrieved Chunk:** Chunk trong General Privacy Statement mô tả các quyền như access, correction, deletion, objection, restriction; query này dùng metadata filter `policy_type=privacy`.  
**Score:** `0.6607`  
**Relevant:** Yes  
**Agent Answer (actual):**
> **Privacy rights that users generally have over their personal data**
>
> | # | Right | What it lets you do |
> |---|-------|---------------------|
> | 1 | **Right to Know / Access** | Ask a company to disclose the personal information it holds about you. |
> | 2 | **Right to Request Correction** | Correct or update inaccurate or incomplete personal data. |
> | 3 | **Right to Erasure / Right to be Forgotten** | Ask a company to delete your personal data in certain circumstances. |
> | 4 | **Right to Restrict Processing** | Limit how the company uses or shares your data. |
> | 5 | **Right to Object** | Oppose the processing of your data, especially for marketing or profiling. |
> | 6 | **Right to Data Portability** | Obtain a copy of your data in a machine-readable format and transfer it elsewhere. |
> | 7 | **Right to Know Recipients** | Learn who the company shares your data with. |
> | 8 | **Right to Withdraw Consent** | Revoke consent when processing is based on consent. |
> | 9 | **Right to be Informed** | Be told how, why, and for how long your data will be processed. |
> | 10 | **Right to File a Complaint** | Complain to a regulator or seek legal recourse if rights are violated. |
>
> Bottom line: users can ask for a copy of their data, correct or delete it, limit how it is used, know who receives it, withdraw consent, and seek redress if those rights are violated.

**Bao nhiêu queries trả về chunk relevant trong top-3?** 5 / 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> Qua kết quả benchmark, tôi nhận ra một điểm quan trọng là retrieval score cao chưa chắc đồng nghĩa với chunk thật sự mạch lạc. Một strategy như fixed-size có thể đạt hit rate rất tốt, nhưng khi giải thích câu trả lời cho người dùng hoặc đối chiếu với gold answer, việc chunk bị cắt giữa ý vẫn làm grounding khó hơn.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> Điều tôi rút ra là metadata filtering có giá trị rất thực tế trong corpus policy. Ở query về privacy rights, việc lọc `policy_type=privacy` giúp loại bỏ nhiễu từ Terms of Service và đưa đúng tài liệu cần thiết lên top mà không phải phụ thuộc hoàn toàn vào similarity score.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 10 / 10 |
| Chunking strategy | Nhóm | 13 / 15 |
| My approach | Cá nhân | 10 / 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results | Cá nhân | 10 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 4 / 5 |
| **Tổng** | | **87 / 100** |
