## ivweb-ui

This project was built manually, without using a preset build tool
like create-react-app.

Due to time constraints, and lack of holistic planning on upgrading the
as-of-now (2021) Vizor Manager application (written years ago, running
old versions of dependencies), this application is designed to shim in
react functionality over time rather than replace the whole Vizor manager UI.
As such, it needs more flexible build tooling and some manual configuration
not easily supplied with an out-of-the-box tool.

Some code / conventions / configurations were ported from
highwire/platform-administration/core-ui.
