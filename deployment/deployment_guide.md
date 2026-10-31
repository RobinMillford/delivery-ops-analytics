# Public Streamlit deployment guide

The assessment requires the dashboard to open from a public link without a login or access request. This project is prepared for Streamlit Community Cloud deployment, but it has not been deployed because deployment requires the candidate's GitHub / hosting account.

## 1. Put the project in GitHub

1. Create a new GitHub repository.
2. Upload the full `delivery_ops_assessment/` project folder, including `data/`, `src/`, `pages/`, `app.py` and `requirements.txt`.
3. Do not omit the CSVs: the Streamlit app reads them from the local `data/` directory inside the repository.
4. Keep credentials and private files out of the repository. This assessment contains no API keys.

## 2. Deploy the app

1. Open Streamlit Community Cloud and sign in with GitHub.
2. Create a new app and select the repository and branch.
3. Set the app entry point to `app.py`.
4. Deploy. The platform installs packages from `requirements.txt`.
5. In the app settings, ensure the app's visibility is public / accessible to anyone with the link (not restricted to workspace users).

## 3. Verify before submission

Open the generated URL in a private/incognito browser window where you are not signed in. Confirm:
- The page opens without login or an access request.
- All six pages load.
- Hub filters work.
- KPI values agree with the report.
- No file-not-found errors occur.

Copy the public URL into:
- `report/final_assessment.pdf` (replace the clearly marked deployment placeholder and re-export the PDF).
- The Google Form submission.

## 4. Important

A local URL such as `http://localhost:8501` is not a public dashboard link. Do not submit it as proof of public access.
