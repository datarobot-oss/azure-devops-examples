# Azure DevOps workload pipeline

A pipeline that deploys the app in `app/` to DataRobot as a workload. A pull request prints the plan. A merge to `main` waits for an approval, deploys, and runs a smoke test.

The app is the `backend/` folder of the DataRobot `minimal-app-template`, a FastAPI server with `/` and `/hello`, with its dependencies pinned. Replace it with your own app. The only requirements are a `Dockerfile` at the root of `app/`, a port of 1024 or above, and a `linux/amd64` image.

The pipeline pins `dr` v0.14.1. Steps that no example run covers are marked unverified.

## Files

The following table lists the files in this folder.

| File | Purpose |
| --- | --- |
| `azure-pipelines.yml` | The pipeline, with a Plan stage and an Apply stage. |
| `templates/install-dr.yml` | Installs the pinned `dr` CLI and checks its SHA-256. |
| `app/` | The app, its `Dockerfile`, and its dependencies. |
| `app-java/` | A Spring Boot app with `/` and `/hello`, built by a multi-stage `Dockerfile`. See [Use the Java sample](#use-the-java-sample). |

## Set up the pipeline

Follow these steps once per repository.

1. Deploy once from a workstation to create the workload and the manifest.

   ```sh
   cd app
   dr workload up --yes
   ```

   Commit `app/.datarobot.yaml` and `app/.drignore`. The manifest holds the workload ID. Without it, every pipeline run creates a new workload. Don't commit `app/.datarobot/`.

2. Create a variable group named `datarobot-deploy` in **Pipelines > Library** with two variables:
   - `DATAROBOT_ENDPOINT`, for example `https://app.datarobot.com/api/v2`.
   - `DATAROBOT_API_TOKEN`, marked secret. Use the key of a service account, not a person.

3. Create an environment named `prod` and add two checks on its **Approvals and checks** tab:
   - An Approval, with `requesterCannotBeApprover` on and one approver who isn't the author.
   - An Exclusive lock. Two `dr workload up` runs at the same time fail with HTTP 422.

4. Create a pipeline from `azure-pipelines.yml`. Authorize it to use the variable group and the `prod` environment on its first run.

5. Add a build validation policy on `main` that runs the pipeline. A pull request then prints the plan. The Plan stage runs the pipeline file from the pull request branch with the secrets of the variable group, so limit who can push branches and keep secrets off for builds of forks.

## Use the Java sample

The `app-java/` folder deploys through the same pipeline. The image builds inside the `Dockerfile`, so the agent needs no JDK or Maven.

1. Run step 1 of the setup in `app-java` and commit `app-java/.datarobot.yaml`.
2. Run the pipeline with the `appDir` parameter set to `app-java`. To make it the default, change the `default` of the parameter.
3. (Optional) If you build the jar on your workstation, add `target` to `app-java/.drignore`, so the sync doesn't upload it.

The runtime stage runs as a non-root user and listens on port 8080. To replace the sample with your own Spring Boot app, keep the `Dockerfile` shape: a Maven or Gradle build stage and a JRE stage.

## What a run does

The following table shows what each trigger runs.

| Trigger | Plan stage | Apply stage |
| --- | --- | --- |
| Pull request to `main` | Runs `dr workload up --dry-run` and prints the plan. | Skipped. |
| Push to `main` that changes `app/` or `app-java/` | Same. | Waits for the approval, runs `dr workload up --promote`, then calls `/hello` until it answers 200. |

A deploy takes about 8 minutes, mostly the rollout. Every run uploads the code again, because a CI checkout has no `.datarobot/` cache, so a run with no code change still rolls a new version. The `app/**` and `app-java/**` path filters keep unrelated commits from starting a deploy.

## Parameters

The following table lists the pipeline parameters.

| Parameter | Default | Use it for |
| --- | --- | --- |
| `selfHostedPool` | Empty, a Microsoft-hosted `ubuntu-24.04` agent. | The name of a self-hosted pool, never the environment name. Unverified: no self-hosted agent was tested. |
| `drSecureFile` | Empty, `dr` downloads from GitHub. | The name of a Secure file that holds the `dr` release tarball, for a network that can't reach GitHub. Unverified: the Secure file branch was never run. |
| `appDir` | `app` | The directory to deploy. Set `app-java` for the Spring Boot sample, or the folder of your own app. |

To change the `dr` version, update `DR_VERSION` and `DR_TARBALL_SHA256` together. The checksum in the file belongs to `dr_v0.14.1_Linux_x86_64.tar.gz`, taken from the checksums file of the release.

## Limits

These limits apply to the pipeline.

- A self-hosted agent needs `bash`, `curl`, `tar`, and `sha256sum`, and a route to the DataRobot endpoint. Unverified.
- The pipeline needs a DataRobot release that has `dr workload up` and the Workload API. The CLI reads the Workload API at `/api/v2/endpoints/workloads/`. Check the release with `scripts/check_workload_ready.py`.
- Azure DevOps Server (on premises) runs most of this YAML, but the feature set depends on the version. Unverified.
- Branch policies and checks are settings, not files. Another team can't copy them from this folder, so steps 3 and 5 are manual.
