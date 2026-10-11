# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Streamlit + Plotly (Python), reading aggregated results from MongoDB. Chosen in the project plan (`docs/KE_HOACH_DO_AN_CAI_TIEN.md`, sections 4.5 and 21). Data pipeline: HDFS + Apache Spark (PySpark, MLlib) in Docker Compose.

## Users

- **Primary:** the student team presenting their final Big Data course project, and the lecturer plus classmates watching on a projector or laptop screen during the defense. The presenter drives the dashboard live while telling the story of the data; the audience must read every chart from the back of a room.
- **Role the product plays in the story:** a social-listening tool for a media / marketing analyst who needs to know what people are discussing, and when a topic suddenly spikes.

## Product Purpose

Analyze topics in Vietnamese-language YouTube videos and comments across broad subject areas, track how their volume changes over time, identify bursts, and present interpretable results through a dashboard. The project is an academic sample, not a representative measure of public opinion.

## Positioning

Every number on screen comes from the team's own Spark pipeline over HDFS, with its evidence visible: data-quality funnel, experiment registry, metric-based model choice, burst scores. It shows the method, not just pretty charts.

## Operating Context

- Live demo in the course defense (week 10), plus screenshots inside the Word report and slides.
- The dashboard must run without the Spark cluster: it reads MongoDB, and the Text Analyzer loads a local copy of the model.
- Dataset: public YouTube videos and top-level comments found through YouTube Data API v3 queries in seven topic areas. The analysis window and resulting sample are determined by the local collection configuration.

## Capabilities and Constraints

- Six pages: Bảng điểm (scoreboard), Các câu chuyện (topics), Diễn biến (trends), Từ khóa & Hashtag, Phân tích văn bản (Text Analyzer), Dữ liệu & Phương pháp (data quality, experiments, scalability). No geographic page: the dataset has no location field.
- Presentation mode (default on) hides adult content and masks profanity on screen; statistics are unchanged.
- Every chart carries a data-driven insight sentence.
- KMeans output must never be shown as probability; LDA shows a topic distribution.
- Results describe only the studied dataset, never "public opinion" in general.
- Two-person student team, 10 weeks; academic integrity rule: code written by the team.

## Brand Commitments

None. Interface language is Vietnamese; technical terms (TF-IDF, LDA, KMeans, burst, NPMI) stay in English.

## Evidence on Hand

- YouTube API data is stored locally and excluded from Git. Processed outputs are regenerated from the current collection before a dashboard demo.
- Topic labels in `config/topic_labels.yaml` are proposals pending the team's joint review. Insights on screen are generated from pipeline output; never fabricate them.

## Product Principles

1. Evidence over decoration: each view should be defensible under questioning from the lecturer.
2. Legible from the back of the room: projector-first readability.
3. Honest scope: show limitations (bias, heuristics, logical cluster) rather than overclaim.
4. Story order: from data quality → topics → time trends → bursts → applying the model to new text.

## Accessibility & Inclusion

Projector use: high contrast, large type, color never the only carrier of meaning (topic colors also carry labels).
