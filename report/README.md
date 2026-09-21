# Instructions to generate the final report

## Install Dependencies
### Install Pandoc 3.11 or greater
https://github.com/jgm/pandoc/releases/tag/3.11

#### Verify Pandoc is installed
From a terminal window run: 'pandoc --version'

### Install MikTek for PDF generation
https://miktex.org/download

#### Verify MikTek is Updated
Open the MikTek Console app.
Select the "Updates" tab.
Click "Update Now"

## Run the report generator

### Run the HTML report generator
From a terminal window run: 'pandoc --defaults report/pandoc.yaml -o report/generated-report/final.html'

This is NOT the official report. This is just a quick report generator to view the changes without the MikTek dependency. The official report is the final.pdf.

### Run the Word Doc report generator
From a terminal window run: 'pandoc --defaults report/pandoc.yaml -o report/generated-report/final.docx'

This is NOT the official report. This is just a quick report generator to view the changes without the MikTek dependency. The official report is the final.pdf.

### Run the PDF Official report generator
From a terminal window run: 'pandoc --defaults report/pandoc.yaml --pdf-engine=xelatex -o report/final.pdf'

On the first build, you may need to install several MikTek packages to successfuly generate the report