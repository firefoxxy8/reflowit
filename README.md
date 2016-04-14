# ReflowIt

This project contains the code for a proof of concept project developed for and
around a Hack Day conducted at the New York Public Library on Jan 14, 2015. The
POC is intended to explore one possible solution for the problem of using
digitized texts on small form devices such as smartphones. For this POC we
targeted the JSTOR public domain content
(http://about.jstor.org/service/early-journal-content) hosted by the Internet
Archive (https://archive.org/details/jstor_ejc). While the JSTOR PD content was
used as the source data in this POC the scope of problem is much broader in
that many 10's (or even 100's) of millions of documents are only available as
PDFs of scanned page images.

Page scan PDFs provide a great means for distributing documents for printing
and off-line reading. Using them for on-line reading is cumbersome on devices
other than desktops, laptops and larger tablets. This POC is specifically
targeting the feasibility of reformatting these PDFs for use with smartphones
and smaller e-readers. This project includes scripts for reflowing an original
PDF into a mobile-optimized PDF and then extracting the resulting pages into
individual image files suitable for viewing on mobile devices in both web and
native apps.

** Original demo
The original demo of this POC can be seen at http://labs.jstor.org/reflowit.
This is best viewed from a smartphone (which is the whole point of this, right?)
The POC consisted of a simple web app (using Django and JQuery Mobile) for
viewing the original and reflowed pages for a handful of articles. The app
supports toggling between the original and mobile views. The PDF reflowing is
performed by the open source tool ‘k2pdfopt’ (http://www.willus.com/k2pdfopt/).
This POC includes a wrapper script (in python) that fetches an original PDF
from the Internet Archive and invokes k2pdfopt and imagemagick to perform the
PDF reflowing and image extraction. The wrapper also provides some conveniences
for syncing the generated output with an AWS S3 data store for use by web
applications. The wrapper script also includes some initial support for defining
and managing configuration profiles for optimizing generated content for
specific devices or classes of device.

## Restructured code base

Since the original POC was developed the code has been refactored to
achieve a cleaner separation between the conversion and viewing.  The conversion
process is now implemented as a web service that accepts as input a URL to
a PDF and returns a JSON object with links to the generated PDF and extracted
image files (for both the original and mobile-optimized PDFs).

### Server

#### AWS Lambda

### Client

#### Angular JS

#### GitHub Pages
