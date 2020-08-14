# Election Contacts
![](https://github.com/vote-by-mail/election-official-data/workflows/Python%20CI/badge.svg)
![](https://github.com/vote-by-mail/election-official-data/workflows/Public%20data/badge.svg)

This repo collects information by locale (county or town) from critical swing states for [VoteByMail.io](https://votebymail.io).  Code for each state is under the state's name.

## Getting Started
To get started, run the `make create-install` command.  There are other useful commands there.

The real work is done by [PyInvoke](http://www.pyinvoke.org/), a simple task runner which was installed by the previous command.

## Data Format
Data is saved in the `/public` folder of the [public-data branch](https://github.com/vote-by-mail/election-official-data/tree/public-data) by state (e.g. `florida.json`).  Each file is a json array of all election-official contacts for locale.  The format of the contacts depends on the state but supports (at a minimum) the following `typescript` interface
``` ts
interface Contact {
  // each contact should have a locale and either a county or city
  // it should also have either an email or fax and preferably the county official's name.
  locale: string            // locale name, unique within state
  county?: string           // county name
  city?: string             // city or township name
  official?: string         // name of election's official
  emails?: string[]         // array of emails
  faxes?: string[]          // list of fax numbers in E.164 format + ext

  // optional fields
  phones?: string[]         // list of phone numbers in E.164 format + ext
  url?: string              // url for locale's election information
  address?: string          // mailing address data
  physicalAddress?: string  // physical address
  party?: string            // party affiliation of official
}
```
**NB:**, fields with a question mark (e.g. `county?`) indicate that the value may possibly be empty, i.e. no such key exists.  If no values are provided by the state, this is how it is indicated.

Phone and fax numbers should be in [E.164 format](https://en.wikipedia.org/wiki/E.164), with optional extensions allowed. Since all numbers are US, they should match the regex `'^\+1\d{10}(x\d+)?$'`. Collecting a state calls `normalize_state` in `src/common.py`, which will automatically reformat phone and fax numbers that are close to this format.

State data is no longer saved in the `master` branch of this repo.

Data releases are tagged with the date of collection using the format `data/yyyy-mm-dd`. Files that could not be collected or had no changes will be carried over from previous commits.

## Adding a New State
Each state's crawler is put under its own folder (e.g. `states/new_york/main.py`), with potentially other files in the folder.
- The goal is for each state's crawler to fetch and process all of its required inputs without human intervention, so that we can easily re-run scripts periodically to collect fresh data.
- We use `cache_request` from `common.py` to request webpages so that the results are saved to a local cache for faster development. The `common` module also contains several other functions which may be useful, including `cache_selenium` and `cache_webkit`.
- Each state's `main.py` should include a function named `fetch_data()`, which will be called using PyInvoke using (e.g.)

  ```inv collect new_york```

- The results are then sorted using `normalize_state` from `common.py` and saved in the above [json format](#Data_Format).
- Once you have the data, verify that it works by running tests:

  ```make test```

- Also, rerun the Jupyter notebook `analysis/Analysis.ipynb` from scratch to update the analytics.  You can see how many fields you were able to parse.  To start the jupyter notebook, run `make jupyter`.  Run the notebook.  Make sure that you have all the values you need.  **Do not commit the notebook changes**.  Jsut throw them away.  They just block rebase merging.

## Refreshing Data between Scheduled Runs
The `public_data` GitHub Actions workflow will periodically run, collect fresh data, commit any updated .json files to the `public-data` branch, and push a new data version tag in the format `data/yyyy-mm-dd`.

To trigger this workflow between scheduled runs (i.e., after a new state is added to `master`), push any commit to the `trigger-public-data` branch. This will run the update workflow based on the latest code on master branch (admittedly, this is a bit of a hack to trigger a github action). If updated data is found, this will also push a new data version tag as part of the normal workflow.

For example,

```bash
git checkout trigger-public-data
touch 20200714_unscheduled_run.txt
git add 20200714_unscheduled_run.txt
git commit -m "20200714 unscheduled run"
git push origin trigger-public-data
```

This will automatically create a tag with the updated data and proper date.

### Manually collecting data locally
Some state code (i.e. Nevada) does not seem to work on Github Actions.  Instead, it needs to be run manually.  To do this, you must run the following commands (changing values for the tag as necessary)
```
git checkout master
inv collect nevada
cp public/nevada.json /tmp/.
git checkout public-data
cp /tmp/nevada.json public/.
git commit -am 'Adding Nevada'
git tag data/2020-08-07
git push origin data/2020-08-07
```

## Notes on Submitting Code
Please submit code via pull requests, ideally from this repo if you have access or from your own fork if you do not.
- This repository has a continuous integration (CI) workflow to run pylint and tests on pull requests.  The tests must pass for CI for code to be merged.
- We strive to only use [rebase merges](https://git-scm.com/book/en/v2/Git-Branching-Rebasing)
- Please don't save changes to the Jupyter notebook `analysis/Analysis.ipynb` (it will break your rebase merge).

## Notes on Deploying
To update a version, tag the commit with a bumped [semvar version](https://semver.org/) and push the tag.  Admittedly we are a little loose on the definition of a "minor" vs "patch" increment.  For example, if the previous version was `1.4.0` and we chose to increment to `1.5.0`, we would deploy using:
```bash
git tag v1.5.0
git push origin v1.5.0
```
To see a list of all tags, run
```bash
git fetch
git tag --list
```
<b style='color: red;'>DO NOT DELETE TAGS ONCE THEY ARE PUBLISHED!</b>
Just increment the minor version and republish if you made a mistake.  We rely on stable tags for production.

## Usage
- To get started, look at the `Makefile`.  You can install files, startup Jupyter, etc ...
- To run tasks, we use [PyInvoke](http://www.pyinvoke.org/).  Look at `tasks.py` file

## About Us
This repository is for [VoteByMail.io](https://votebymail.io).

## Contributors
- [tianhuil](https://github.com/tianhuil/)
- [twagner000](https://github.com/twagner000/)
- [Luca409](https://github.com/Luca409/)
