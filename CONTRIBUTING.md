# Contributing Guidelines

Guidelines for developing and contributing to this project.

## List of project maintainers

- [Andrii Kislitsyn](https://github.com/andriykislitsyn)
- [Carson Gee](https://github.com/carsongee)

## Where to contribute

Contribute on GitHub. Open an issue before a large change, such as a new example, so a maintainer can confirm that it fits.

## Keep the examples honest

Each README states what was run and marks the rest as unverified. When you change a pipeline, run it on Azure DevOps and update that statement. If you couldn't run a step, say so in the README and in the pull request.

Each folder under `templates/` is meant to be copied as the root of its own repository. Don't link from one folder to a file outside it, except to the README of the sibling example.

## Running the checks

CI runs these checks on every pull request. Run them locally before you push.

| Check | What it covers | Run it with |
| --- | --- | --- |
| markdownlint | Every Markdown file | `npx markdownlint-cli2 "**/*.md"` |
| yamllint | Every YAML file, including the pipelines | `uvx yamllint==1.32.0 --strict .` |
| zizmor and actionlint | The workflows and the Dependabot config | The `workflow-lint` workflow. The image digests are in `.github/workflows/workflow-lint.yml`. |
| Sample builds | The `Dockerfile` of each sample app | `docker build --platform linux/amd64 templates/azure-devops-workload/app` |
| gitleaks | The full git history | The `secret-scan` workflow. |

## Opening new issues

- Before opening a new issue, check the existing issues and pull requests.
- Use the issue template that fits, and fill in every field.
- Be as specific and detailed as possible. Redact tokens and customer data from logs.

## Did you find a bug?

- Do not open a GitHub issue if the bug is a security vulnerability. Follow [SECURITY.md](SECURITY.md).
- Ensure the bug was not already reported in the Issues section.
- Open an issue as described above.

## Responding to issues and pull requests

This project is community maintained. Maintainers respond on a best-effort basis, with no response-time commitment.

If your issue or pull request gets no response, you can email oss-community-management@datarobot.com.
