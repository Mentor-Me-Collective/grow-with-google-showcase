How to test this locally:
1. Clone the repo and pull the new online branch:
If you haven't already, clone the repository and move into the project folder:

git clone https://github.com/Jolitomi/Biodiversity_Planner.git
cd Biodiversity_Planner

Then, fetch the latest updates and switch to my new branch:

git fetch origin
git checkout feature/automation-web-ui

2. Install the required dependencies:
Make sure you have both Streamlit and Pandas installed in your environment:

python -m pip install streamlit pandas

4. Run the web application:
You must run this from the absolute root of the repository (Biodiversity_Planner/) so the relative file paths to the data/processed/ folder map correctly:

streamlit run app/app.py
The application will automatically open in your default web browser (typically at http://localhost:8501)
## 🚀 Running the Application

### Clone the Repository

```bash
git clone https://github.com/Jolitomi/Biodiversity_Planner.git
cd Biodiversity_Planner
```

### Create a Virtual Environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Launch the Application

```bash
streamlit run app/app.py
```
