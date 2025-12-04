# cPanel Deployment Instructions

Follow these steps to configure your Python application on cPanel after running the `deploy.sh` script.

## 1. Run Deployment Script
Run the deployment script to upload the files to your server:
```bash
./deploy.sh
```
*Note: Ensure you have the SSH key (`~/.ssh/id_rsa_deploy`) configured and the variables in `deploy.sh` match your server details.*

## 2. Setup Python App in cPanel
1. Log in to your cPanel.
2. Go to **"Setup Python App"** under the Software section.
3. Click **"Create Application"**.
4. Configure the following:
   - **Python Version**: Recommended 3.13.
   - **Application Root**: `funding-rate` (matches the `DEST_PATH` in `deploy.sh`).
   - **Application URL**: Select your domain (e.g., `funding.fixsimu.com` or `fixsimu.com/funding`).
   - **Application Startup File**: `passenger_wsgi.py`
   - **Application Entry Point**: `application`
5. Click **"Create"**.

## 3. Install Dependencies
1. In the "Setup Python App" page, scroll down to "Configuration files".
2. In the input box, type `backend/requirements.txt` and click **"Add"**.
   *Note: If it doesn't find it, ensure the file exists at `funding-rate/backend/requirements.txt`. You might need to use the full path or just `requirements.txt` if you moved it.*
   *Since our structure is `backend/requirements.txt`, try entering that. If cPanel requires it at root, you may need to move it or symlink it via SSH.*
   
   **Alternative (SSH):**
   SSH into your server and run:
   ```bash
   source /home/akilnoqy/virtualenv/funding-rate/3.9/bin/activate
   pip install -r ~/funding-rate/backend/requirements.txt
   ```

## 4. Environment Variables
In the "Setup Python App" page, add the following Environment Variables:
- `FLASK_ENV`: `production`

## 5. Restart Application
Click the **"Restart"** button in the Python App configuration page.

## 6. Verify
Visit your URL. You should see the Funding Rate Dashboard.

## Troubleshooting
- **Static Files 404**: Ensure `frontend/dist` was uploaded correctly to `~/funding-rate/frontend/dist`.
- **Internal Server Error**: Check the `stderr.log` in your application root (usually `~/funding-rate/stderr.log`) or the cPanel error log.
