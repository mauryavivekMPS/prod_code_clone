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

    npm install

The above command (and all others described in this readme)
should be run within the impactvizor-pipeline/ivweb-ui
directory.

Insall [parcel-builder](https://parceljs.org/) globally:

    npm install -g parcel-bundler

This will make the parcel command available. Use it to run a development server:

    parcel index.html

The index.html file is useful for development only, in cases where quick-cycling
UI development needs to be done in an isolated manner, and with the convenience
of modern front-end build tools, outside the overall Vizor Manager / ivweb
Django application.

Note that due to Cross-Origin Resource Sharing (CORS) issues with browsers,
some commands that would cause an Ajax call to the Django application will
not work in the local development mode. This is because the local dev
instance by default runs on port 1234, and a Vizor Manager instance running
on localhost:8000 will be considered another domain by your browser.


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

For the immediately forseeable future, these built files will be checked into
version control. While generally front end projects avoid checking built
artifacts into version control, in our case this offers several advantages.

First, the rest of our UI is using old tooling like bower, an old version of
npm, and Grunt. These tools will not work to build this newer UI component.

Second, as has been seen throughout the life of this now 25 year old
technology company, people come and go and code may run for decades. If that
ever becomes the case for this UI, we'll have a built copy and we won't have to
worry about someone 10 years from now struggling to combile the code from
source. 
