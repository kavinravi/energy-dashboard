# Energy Dashboard Setup Instructions

Follow these steps to set up your automatically updating energy dashboard:

## 1. Create a GitHub Repository

1. Go to [GitHub](https://github.com) and sign in
2. Click the "+" icon in the top right, then "New repository"
3. Name it `energy-dashboard` (or any name you prefer)
4. Make it public
5. Click "Create repository"

## 2. Push the Code to GitHub

Open a terminal and run these commands:

```bash
# Clone or download this repository
git clone https://github.com/[original-repo]/energy-dashboard.git
cd energy-dashboard

# Point to your new repository
git remote set-url origin https://github.com/YOUR_USERNAME/energy-dashboard.git

# Push the code
git push -u origin main
```

## 3. Set Up Spotify API Credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
2. Create a new app
3. Copy your Client ID and Client Secret
4. Go to your GitHub repository
5. Click "Settings" > "Secrets and variables" > "Actions"
6. Add two new repository secrets:
   - Name: `SPOTIFY_CLIENT_ID`, Value: your Spotify Client ID
   - Name: `SPOTIFY_CLIENT_SECRET`, Value: your Spotify Client Secret

## 4. Enable GitHub Pages

1. Go to your GitHub repository
2. Click "Settings" > "Pages"
3. For Source, select "GitHub Actions"
4. Wait for the first workflow run to complete (you can go to the Actions tab to see progress)

## 5. Share with Your Friend

After the GitHub Action completes, your dashboard will be available at:
`https://YOUR_USERNAME.github.io/energy-dashboard/`

Share this URL with your friend - they can access it from any browser.

The dashboard will update automatically every day, so they'll always see fresh content without you needing to do anything! 