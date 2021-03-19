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

### Development

Install dependnecies using npm:

    npm Install

The above command should be run within the impactvizor-pipeline/ivweb-ui
directory.

Insall [parcel-builder](https://parceljs.org/) globally:

    npm install -g parcel-bundler

This will make the parcel command available. Use it to run a development server:

    parcel index.html

The index.html file is useful for development only, in cases where quick-cycling
UI development needs to be done in an isolated manner, and with the convenience
of modern front-end build tools, outside the overall Vizor Manager / ivweb
Django application.


### Building / Integrating with Vizor Manager

For now, given the size and scope of reworking the entire Vizor Manager UI
with more up to date and modern technologies, we will simply be building
small React components that can be incorporated onto a given page.

Essentially, we just want to build our JavaScript and CSS files and place
them in the static directory of the Django application,
where they can be pulled in to views as needed.

When code changes are ready to integrate into the Vizor Manager Django
application, run the following to build the minified files and
distribute them to the static directory:

    npm run dist
