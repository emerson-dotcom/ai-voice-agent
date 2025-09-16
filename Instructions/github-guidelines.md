GitHub Commit and Pull Request Guidelines
This document outlines the standardized process for managing changes in the GitHub repository. Employees are expected to adhere to these guidelines to ensure clarity, consistency, and maintainability of the codebase.

## Repository Guidelines
### Branch Structure:
- The main branch is the default branch. All finalized changes will be merged into it.
- A staging branch will serve as an intermediate testing ground. All changes must be merged into staging first before being merged into main.
- Feature branches should be created from staging and merged back into staging upon completion.
- After validation, staging will be merged into main.

### Branching Workflow:
1. Create a new branch from staging for each change.
2. Implement changes and commit following the commit guidelines.
3. Open a pull request to merge the branch into staging.
4. Once changes in staging are validated, they will be merged into main.

## Branching Guidelines
### New Branch for Every Change:
- Create a new branch for every change you implement.
- Use clear and descriptive branch names that define the purpose of the branch.
- Remember to `git pull origin main` and then `git checkout -b <branch-name>` to create a new branch based on the latest code.

**Example branch names:**
- fix-login-issue
- add-user-authentication
- update-dashboard-ui

## Commit Guidelines
### Meaningful Commits:
- Each commit must represent a meaningful change to the repository.

### Commit Message Format:
Commit messages must follow this format:

```
<commit name>: <description>
```

- **Commit Name:** A single word summarizing the type of change (e.g., fix, add, update, refactor).
- **Description:** A brief summary of the change, under 15 words.

**Examples:**
- `fix: resolve user login error`
- `add: implement authentication for new users`
- `update: improve dashboard UI layout`

## Pull Request Guidelines
### Testing Requirements:
- Ensure all tests pass before submitting a pull request.
- Add new tests to cover any new code added in the branch.

### Code Review:
- Submit pull requests for review after ensuring all requirements are met.
- Include a brief description of the changes in the pull request description.

### Code Diff and Comments:
- Avoid adding large chunks of code or creating pull requests with large diffs unless absolutely necessary.
- Break down large changes into smaller, manageable pull requests for easier review.
- Resolve all comments on a pull request before it is merged.

## Summary Checklist
### Branch:
- Create a new branch for every change.
- Use clear, descriptive branch names.
- Merge into staging first before merging into main.

### Commits:
- Make meaningful commits with clear messages.
- Follow the commit message format: `<commit name>: <description>`.

### Pull Requests:
- Pass all tests before submitting.
- Add comprehensive tests for new code.
- Avoid large diffs and resolve all comments before merging.

---
By adhering to these guidelines, we maintain a high-quality, collaborative, and well-documented codebase.
