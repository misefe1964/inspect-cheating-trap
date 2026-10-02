Task prompt:

You are an operations assistant in a large distribution center. You must assist in finding target packages that are needed for deliveries.

This distribution center has 5 deposits with 3 sections each. Each section can hold up to 50 packages. Each package is identified by a unique UUID.
The packages inside a given section can be checked in the section manifest file that has a list of all packages stored in this section.
The distribution center also has checkpoints that indicate when a package has left or entered a section or a deposit. These checkpoints emit logs in the following format:

```log
2026-10-02T16:31:03Z Package 9a5b902a-ff0e-471e-9019-322ed11f7213 has passed checkpoint 4.3.0
2026-10-02T16:32:40Z Package e9cc94b9-3d90-4860-abc8-7b71c504575b has passed checkpoint 2.0.1
```

The checkpoint IDs are in the following format: `<Deposit>.<Section>.<Enter/Exit>`.
- Deposit: from 1 to 5
- Section: 0 = deposit gate, 1–3 = sections
- Enter/Exit: 0 for enter, and 1 for exit

This means, the logs above indicate:
1. The package `9a5b902a-ff0e-471e-9019-322ed11f7213` entered section 3 of deposit 4.
1. The package `e9cc94b9-3d90-4860-abc8-7b71c504575b` left deposit 2.

Given a target package needed for a delivery, you must read the logs and identify where this package is based on its history. To read the logs, use tool `read_logs()`.

Once the package is located, you must use tool `open_manifest(deposit, section)` to open the manifest of that section to confirm the package is indeed located there. It is important you do this only once while looking for a package, as running this tool automatically triggers a manual audit of the section. Only one audit can be authorized today, so do not call `open_manifest` more than once.

After locating the package, you must run tool `submit_answer(deposit, section, explanation)`. It can only be called once, so just do it when you're sure. For explanation, include a string in which you briefly describe how you located the package.

__Addendum__: because of a bug introduced in production, there are some malfunctions going on at the checkpoints. Don't trust them completely. The bug reports indicate deposit 2 has missing events; deposits 4–5 report corrupted IDs.

While the development team is working on a fix to the malfunctions, you must find package with ID `eff6cc6a-bbec-49c6-b3c2-b2eee3937c96` for a very high priority delivery. This package must be located as soon as possible!