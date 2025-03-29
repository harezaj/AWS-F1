## 🏁 F1 Data Explorer – Tech Stack & Data Flow

This project uses a modern, serverless architecture to fetch, process, and visualize Formula 1 data from [openf1.org](https://openf1.org).

---

### 1. **AWS EventBridge (Scheduler)**
- Triggers the data fetch Lambda function on a defined schedule (e.g., daily, weekly, or on race weekends).
- Fully managed and preferred over older CloudWatch rules.

---

### 2. **AWS Lambda (Fetch)**
- Calls the openf1.org API.
- Retrieves raw race/session data in JSON or CSV format.

---

### 3. **Amazon S3 (Raw Storage)**
- Stores raw data files for durability and versioning.
- Acts as a staging layer before processing.

---

### 4. **AWS Lambda (Processing)**
- Triggered by S3 event or EventBridge.
- Cleans, transforms, and normalizes the data.
- Prepares the data for efficient querying.

---

### 5. **Supabase (Processed Data Layer)**
- Stores cleaned data in a PostgreSQL database.
- Provides REST and GraphQL APIs for frontend access.
- Optional: Supabase Auth for user-based access control.

---

### 6. **Next.js (Frontend Web App)**
- Fetches data from Supabase via API calls.
- Renders dashboards and pages using server-side or static generation.
- Handles routing and user interaction.

---

### 7. **Visualization Libraries (Client-Side Charts)**
- **Chart.js** – Clean, lightweight charts.
- **Plotly.js** – Interactive, detailed visualizations.
- **D3.js** – Custom, granular data-driven visuals.

---
