# Optional HPC execution

SMAIRT keeps local execution as the default. Its HPC support is a small Slurm transport for a
declared protocol that already runs correctly; it is not a general scheduler abstraction.

## Configure a submit host

Profiles are user-local and may use native Slurm commands on a login node or an existing OpenSSH
host alias:

```bash
smairt setup hpc configure default --mode native --remote-root /shared/smairt-jobs
smairt setup hpc configure lab --mode ssh --host lab-login \
  --remote-root /shared/smairt-jobs
```

The SSH alias must already be secured in `~/.ssh/config`. SMAIRT uses batch mode and strict
host-key checking and does not accept passwords or credentials in command arguments.

## Submit and reconcile work

```bash
smairt run --backend slurm --compute-profile lab \
  --cpus 4 --memory-mib 8192 --time-minutes 60 -- python analysis.py
smairt hpc status RUN_ID
smairt hpc sync RUN_ID
smairt hpc cancel RUN_ID --yes
```

Submission reserves an immutable local run, records the scheduler job, and copies declared
protocol, configuration, entrypoint, and input files. `status` observes scheduler state. `sync`
explicitly retrieves terminal outputs and finalizes the local manifest. `cancel` is a separate
confirmed mutation.

Cluster policy, modules, containers, allocation names, data governance, queue selection, and
scientific resource adequacy remain the researcher's responsibility. Local paths and credentials
are not exposed through MCP.

SMAIRT targets the documented `sbatch`, `squeue`, `sacct`, and `scancel` interfaces. See the
[Slurm documentation](https://slurm.schedmd.com/documentation.html).
