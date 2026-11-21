# Faceless AI Studio Step 3

This package adds a genuine MP4 renderer using the original Faceless Shorts examples.

## iPhone setup (one time)

1. Upload `Faceless_AI_Studio_Step3.zip` to the ROOT of your **PUBLIC** `faceless-ai-studio` GitHub repository.
2. Open your repository -> Code -> Codespaces -> Create codespace on main (or open an existing one).
3. In Codespaces: Terminal -> New Terminal.
4. Paste:

```bash
unzip -o Faceless_AI_Studio_Step3.zip
rm Faceless_AI_Studio_Step3.zip
git add .
git commit -m "Connect six style renderer"
git push
```

5. Return to your GitHub Pages site. It may take a short while to publish the new `index.html`.
6. Enter a prompt (max 280 characters), pick a style, choose 5 seconds, tap **Generate MP4 via GitHub**.
7. GitHub opens a new Issue with your settings prefilled. Tap **Submit new issue** (signed in as repository owner).
8. Visit your repository -> Actions -> Render Faceless Video -> newest run -> Artifacts -> download ZIP containing MP4.

## Important limitations

- The issue, prompt and logs are **public** because the repository is public. Do not submit private information.
- This initial working renderer uses the Skill's ORIGINAL example character/scene movements. Your prompt becomes a title overlay; it does NOT yet create new character actions or AI-written scripts from the prompt.
- The original six styles are retained in the ZIP. First build may fail due to Chrome, performance, or upstream dependency changes. Check the Action log if so.
- Standard GitHub-hosted Actions on public repositories are currently free, but GitHub enforces abuse and resource limits.
- Do not create an API token or paste credentials into the web page.
