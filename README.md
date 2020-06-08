![](https://github.com/mail-my-ballot/elections-officials/workflows/Python%20application/badge.svg)

# Election Contacts
This repo collects information by locale (county or town) from critical swing states for [MailMyBallot.org](https://mailmyballot.org).  Code for each state is under the state's name.

## Getting Started
To get started, run the `make create-install` command.  There are other useful commands there.

The real work is done by [PyInvoke](http://www.pyinvoke.org/), a simple task runner which was installed by the previous command.

## Data Format
Data is saved in the `/public` folder by state (e.g. `florida.json`).  Each file is a json array of all election-official contacts for locale.  The format of the contacts depends on the state but supports (at a minimum) the following `typescript` interface
``` ts
interface Contact {
  // each contact should have a locale and either a county or city
  // it should also have either an email or fax and preferably the county official's name.
  locale: string            // locale name, unique within state
  county?: string           // county name
  city?: string             // city or township name
  official?: string         // name of election's official
  emails?: string[]         // array of emails
  faxes?: string[]          // list of fax numbers

  // optional fields
  phones?: string[]         // list of phone numbers
  url?: string              // url for locale's election information
  address?: string          // mailing address data
  physicalAddress?: string  // physical address 
  party?: string            // party affiliation of official
}
``` 
**NB:**, fields with a question mark (e.g. `county?`) indicate that the value may possibly be empty, i.e. no such key exists.  If no values are provided by the state, this is how it is indicated.

## Adding a New State
Each state's crawler is put under it's own folder (e.g. `states/new_york/main.py`) with potentially other files in the folder.
- We use `cache_request` to reqeust webpages so that the results are saved to a local cache for faster development.
- You can invoke the file using PyInvoke, i.e. 

  ```inv collect new_york```

- The results are then saved in the above [json format](#Data_Format).
- Once you have the data, verify that it works by runnin tests:

  ```make test```

- Also, rerun the Jupyter notebook `analysis/Analysis.ipynb` from scratch to update the analytics.  You can see how many fields you were able to parse.  To start the jupyter notebook, run `make jupyter`.  Run the notebook.  Make sure that you have all the values you need.  **Do not commit the notebook changes**.  Jsut throw them away.  They just block rebase merging.

## Notes on Submitting Code
Please submit code via pull requests, ideally from this repo if you have access or from your own fork if you do not.
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

## Some State-Specific Information

### Florida
- [Vote by Mail](https://dos.myflorida.com/elections/for-voters/voting/vote-by-mail/)
- [County Supervisors](https://dos.elections.myflorida.com/supervisors/)

### Maine
- [Vote by Mail](https://www.maine.gov/sos/cec/elec/voter-info/absenteeguide.html)
- [Municipal Clerks](https://www.maine.gov/sos/cec/elec/munic.html) (with a link to download them as a CSV)

### Michigan
- They seem to accept email applications [Election Official's Manual](https://www.michigan.gov/documents/sos/VI_Michigans_Absentee_Voting_Process_265992_7.pdf)
- "Michigan residents who live in unincorporated places register to vote with their township clerk": [MI SOS](https://www.michigan.gov/documents/sos/ED-106_Circulating_CityTwp_Nom_+_Qual_Pet_Forms_647901_7.pdf)
- The City-type matters: there is a St. Joseph Township and City, both in Berrien County.  They share a zipcode (Wikipedia [Township](https://en.wikipedia.org/wiki/St._Joseph_Charter_Township,_Michigan), [City](https://en.wikipedia.org/wiki/St._Joseph,_Michigan))
- The following Address is in Olive Township, not West Olive: "12220 Fillmore Street, Room 130 West Olive, MI 49460".
- There is both a [Sheridan Chatter Township](https://www.google.com/maps/place/Sheridan+Charter+Twp,+MI+49412/@43.4237592,-87.1002624,8z/data=!4m5!3m4!1s0x881941cfc5fb3d8f:0x28cee802764453b8!8m2!3d43.4229492!4d-85.9815339) as well as a [Sheridan Township](https://www.google.com/maps/place/Sheridan+Township,+MI+49224/@42.2906076,-87.0140035,7z/data=!4m5!3m4!1s0x883d50194df74c53:0x5d349c5515a24204!8m2!3d42.295598!4d-84.7942091), which are quite far apart.  Similarly for Caledonia, Shelby, Lincoln, Lake, and Benton.

### Georgia
- Contact info for county board of registrars offices [website](https://elections.sos.ga.gov/Elections/countyregistrars.do).

### Virginia
- Contact info available [here](https://vote.elections.virginia.gov/VoterInformation/PublicContactLookup)

### Wisconsin
- Municipal Clerk Lookup ([API](https://myvote.wi.gov/en-US/MyMunicipalClerk))
- Municipal Clerk List ([PDF](https://elections.wi.gov/sites/elections.wi.gov/files/2020-03/WI%20Municipal%20Clerks%20no%20emails%20Updated%203-23-2020.pdf))
- County Clerk List ([PDF](https://elections.wi.gov/sites/elections.wi.gov/files/2020-03/WI%20County%20Clerks%20no%20emails%20Updated%203-23-2020.pdf))

## Usage
- To get started, look at the `Makefile`.  You can install files, startup Jupyter, etc ...
- To run tasks, we use [PyInvoke](http://www.pyinvoke.org/).  Look at `tasks.py` file

## About Us
This repository is for [MailMyBallot.org](https://mailmyballot.org), a [National Vote at Home Institute](https://voteathome.org) project.

## Contributors
- [tianhuil](https://github.com/tianhuil/)
- [twagner000](https://github.com/twagner000/)
- [Luca409](https://github.com/Luca409/)
