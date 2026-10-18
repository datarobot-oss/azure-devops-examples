# Azure DevOps Custom Application pipeline

A pipeline that deploys the Spring Boot app in `app/` to DataRobot as a Custom Application, with Pulumi and the state in Azure Blob Storage. A pull request prints the plan. A merge to `main` waits for an approval, deploys, and runs a smoke test.

Use it when the DataRobot release has no Workloads, or when Custom Applications already run. For a release with Workloads, use [azure-devops-workload](../azure-devops-workload/README.md).

The pipeline pins Pulumi v3.267.0 and the `datarobot` provider 0.10.45. A self-hosted agent and a tarball upload aren't covered by an example run, and the steps that use them are marked unverified.

## Choose a primitive

DataRobot runs an app as a Workload or as a Custom Application. Pick by release and by what the app is. The following table compares the options.

| Primitive | Pick it when | The pipeline needs | Where |
| --- | --- | --- | --- |
| Workload | The release has Workloads and the app is a container. | `dr` | [azure-devops-workload](../azure-devops-workload/README.md) |
| Custom Application from an image | The release has no Workloads, or the app isn't Python or Node, such as a JVM app. | Pulumi and a state backend | This template. |
| Custom Application from source | The app is Python or Node and runs on a DataRobot base environment, such as the `react-base-app` template. | Pulumi and a state backend | Not in this folder. Use `ApplicationSource` with `baseEnvironmentId` set to the base environment and the app files in `folderPath`. |

Check the release with `scripts/check_workload_ready.py`.

## Files

The following table lists the files in this folder.

| File | Purpose |
| --- | --- |
| `azure-pipelines.yml` | The pipeline, with a Plan stage and an Apply stage. |
| `templates/install-pulumi.yml` | Installs the pinned Pulumi CLI and checks its SHA-256. |
| `templates/fix-file-times.yml` | Sets one file time on `app/`, so an unchanged context gives an unchanged plan. |
| `Pulumi.yaml` | The three DataRobot resources, in the Pulumi YAML language. |
| `app/` | The Spring Boot app and the `Dockerfile` that builds it. |
| `source/start-app.sh` | The one script that starts the app inside the environment. |

## How the deploy works

DataRobot builds the image from `app/Dockerfile`, so the agent needs no Docker. Three resources do the work:

1. `ExecutionEnvironment` builds the image from the folder in `dockerContextPath`.
2. `ApplicationSource` uses that environment as its base and adds `source/start-app.sh`, which runs `java -jar /app/app.jar`.
3. `CustomApplication` runs the source.

Don't use `CustomApplicationFromEnvironment` for this. It fails on create with `Struct defines fields not found in object: required_key_scope_level` in the `datarobot` provider 0.10.43 and 0.10.45.

The source name carries the environment version. A change to `app/` builds a new version, which replaces the source. Pulumi creates the new source before it deletes the old one, and DataRobot answers 409 when two sources share a name.

To upload an image instead, replace `dockerContextPath: app` with `dockerImage: app.tar`, and build the tarball before `pulumi up`:

```sh
docker build --platform linux/amd64 -t app:ci app
docker save -o app.tar app:ci
```

Use the tarball when the DataRobot cluster can't reach the base-image registry or Maven Central. The tarball of the sample is about 350 MB. The pipeline doesn't exercise this path, so it's unverified.

## Set up the pipeline

Follow these steps once per repository.

1. Create a storage account and a container for the Pulumi state:

   ```sh
   az group create --name <group> --location <region>
   az storage account create --name <account> --resource-group <group> --sku Standard_LRS --allow-blob-public-access false
   az storage container create --account-name <account> --name pulumi-state --auth-mode login
   az storage account keys list --account-name <account> --query "[0].value" --output tsv
   ```

2. Create a variable group named `datarobot-deploy` in **Pipelines > Library** with these variables:
   - `DATAROBOT_ENDPOINT`, for example `https://app.datarobot.com/api/v2`.
   - `DATAROBOT_API_TOKEN`, marked secret. Use the key of a service account, not a person.
   - `AZURE_STORAGE_ACCOUNT`, the account name.
   - `AZURE_STORAGE_KEY`, marked secret.
   - `PULUMI_CONFIG_PASSPHRASE`, marked secret. Pulumi encrypts the secrets in the state with it.

3. Create an environment named `prod` and add two checks on its **Approvals and checks** tab:
   - An Approval, with `requesterCannotBeApprover` on and one approver who isn't the author.
   - An Exclusive lock, so two runs never deploy at the same time.

4. Create a pipeline from `azure-pipelines.yml`. Authorize it to use the variable group and the `prod` environment on its first run.

5. Add a build validation policy on `main` that runs the pipeline. A pull request then prints the plan.

The first run creates the Pulumi stack `prod`. Store the passphrase in a password manager as well. Without it, the secrets in the stack are unreadable.

## What a run does

The following table shows what each trigger runs.

| Trigger | Plan stage | Apply stage |
| --- | --- | --- |
| Pull request to `main` | Runs `pulumi preview` and prints the plan. | Skipped. |
| Push to `main` that changes `app/`, `source/`, or `Pulumi.yaml` | Same. | Waits for the approval, runs `pulumi up`, then calls `/hello` on the app URL until it answers 200. |

A deploy takes about 3 minutes, mostly the environment rebuild and the app restart.

## State and locking

Pulumi keeps the state in the `pulumi-state` container. A lock file in the container stops a second update while one runs. The following table lists three cases.

| Case | Result |
| --- | --- |
| A second update starts while the first runs. | The second fails with `the stack is currently locked`, and the first finishes. |
| Two updates start at the same moment. | Both fail with the same message, and nothing runs. |
| A run is killed. | The next run fails on the stale lock. `pulumi cancel` clears it, and the run after that works. |

The lock fails closed, so two runs never change the stack at once. The cost is that two simultaneous starts can both fail. Run one of them again. The Exclusive lock on the `prod` environment keeps two pipeline runs from reaching the apply step at the same time, so this case mostly shows up when Pulumi runs by hand next to the pipeline.

Don't delete the container or lose the passphrase. The state is the only record of which DataRobot objects the stack owns.

## Recover from a failure

The following cases cover common failures.

- **A run was cancelled and the next one reports `the stack is currently locked`.** Run `pulumi cancel --yes` against the stack. It removes the stale lock. Check that no run is still active first. Two runs that started at the same moment can both fail with this message. Run one of them again.
- **A create failed and `pulumi destroy` then fails with 422 on the environment or the source.** A failed `CustomApplication` create isn't in the state, so the application is an orphan that still references them. Delete the application in DataRobot, then run `pulumi destroy` again.
- **The apply times out.** The job timeout is 45 minutes. Open the environment in DataRobot and read its build log.

## Parameters

The following table lists the pipeline parameters.

| Parameter | Default | Use it for |
| --- | --- | --- |
| `selfHostedPool` | Empty, a Microsoft-hosted `ubuntu-24.04` agent. | The name of a self-hosted pool, never the environment name. Unverified: no self-hosted agent was tested. |

To change the Pulumi version, update `PULUMI_VERSION` and `PULUMI_TARBALL_SHA256` together. The checksum belongs to `pulumi-v3.267.0-linux-x64.tar.gz`, taken from the checksums file of the release. To change the provider version, change the `version` of all three resources together.

## Scale up

The sample is one app. A larger project, such as the DataRobot agent application with its agent, MCP server, API server, and web frontend, has many resources and its own Pulumi project.

To use this pipeline for a larger project:

1. Replace `Pulumi.yaml`, `app/`, and `source/` with the Pulumi project of the larger application. Keep the pipeline, the install step, and the variable group.
2. If the project uses a Python Pulumi program, add a step that installs Python and its dependencies before `pulumi preview`. The `pulumi login` and `pulumi stack select` lines stay the same.
3. Change the smoke test to call the URL that the project exports.

Unverified: this was not run with a multi-component project.

## Limits

These limits apply to the pipeline.

- The `datarobot` provider hashes a zip of the Docker context, and the zip carries file times. A checkout writes new times on every run, so without `templates/fix-file-times.yml` each run plans a rebuild of the environment, a replacement of the source, and an update of the app. Keep the step in both stages. The first run after adding it still updates the environment once, because the state holds the old hash.
- A self-hosted agent needs `bash`, `curl`, `tar`, and `sha256sum`, and a route to the DataRobot endpoint, to GitHub for the Pulumi release, and to Azure Blob Storage. Unverified.
- Pulumi downloads the `datarobot` provider plugin from the GitHub releases of `datarobot-community/pulumi-datarobot`, set by `pluginDownloadURL` in `Pulumi.yaml`. The default Pulumi plugin host doesn't have it and answers 403, so a fresh agent fails without that setting. A network without access to GitHub needs the plugin installed first from a mirror, with `pulumi plugin install resource datarobot v0.10.45 --server <mirror>`. Unverified: the mirror.
- The DataRobot cluster builds the image, so it needs access to the registry of the base images and to the package repositories.
- Azure DevOps Server (on premises) runs most of this YAML, but the feature set depends on the version. Unverified.
- Branch policies and checks are settings, not files. Another team can't copy them from this folder, so steps 3 and 5 are manual.
