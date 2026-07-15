# Optional HPC execution

SMAIRT keeps local execution as the default. HPC support is a small Slurm transport for a protocol
that already runs correctly; it is not a scheduler abstraction and the end-to-end demo does not
require a cluster.

Configure either a native Slurm login node or an existing OpenSSH host alias in user-local setup:

```bash
smairt setup hpc configure default --mode native --remote-root /shared/smairt-jobs
smairt setup hpc configure lab --mode ssh --host lab-login --remote-root /shared/smairt-jobs
```

The SSH alias must already be secured in `~/.ssh/config`; SMAIRT uses `BatchMode` and strict host-key
checking and does not accept passwords or credentials in commands. Submit only typed resource
options:

```bash
smairt run --backend slurm --compute-profile lab --cpus 4 --memory-mib 8192 --time-minutes 60 -- python analysis.py
smairt hpc status RUN_ID
smairt hpc sync RUN_ID
smairt hpc cancel RUN_ID --yes
```

Submission reserves an immutable local run, records the scheduler job, and copies only declared
protocol/configuration/entrypoint inputs. `status` observes scheduler state; `sync` explicitly
retrieves terminal outputs and finalizes the local manifest. Local paths and credentials remain
unavailable through MCP. Cluster policy, modules, containers, allocation names, data governance,
and scientific resource adequacy remain the researcher's responsibility.

SMAIRT targets the documented `sbatch`, `squeue`, `sacct`, and `scancel` interfaces. See the
[Slurm documentation](https://slurm.schedmd.com/documentation.html).
