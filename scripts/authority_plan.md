# Authority plan

Checked 21 October 2026. This is a link-earning audit and a pitch list. It does not change pages other than the Vail hub in the same pull request, and it does not change `.github/workflows/static.yml`.

The goal is a site that earns links because the guides cite primary sources, and that gives those sources a useful page to link back to. Homepage `index.html` and the app screens stay out of this work.

## What limits link-earning

### Finished guides name sources and do not link them

The visitor guides that are already on the template end with a sources line. None of those lines are links. Checked on this date, these pages have no outbound link except Google, fonts, or CDNs:

- `pages/bronco-buster-statue/index.html`
- `pages/the-lady-doctor-statue/index.html`
- `pages/man-and-woman/index.html`
- `pages/cowboy-in-pajamas/index.html`
- `pages/the-newsboy-statue/index.html`
- `pages/sensory-park/index.html`
- `pages/eagle-statue/index.html`
- `pages/albert-einstein-statue-vail-co/index.html`
- `pages/landmarks/index.html`
- `pages/landmarks/denver/index.html`

Across the repo, 213 of 289 HTML files have no link to a real external site. Under `pages/`, 31 of 62 pages have no outbound citation. A directory that only names Civic Center Conservancy, RTD, or Vail Daily, without linking, gives those sites no reason to link back.

The Vail hub in this pull request is the exception: its sources are normal follow links.

### Thin pages, and a stale queue

48 HTML files are under 180 words of visible text. The worst content stubs are about 10 words: `CO/Landmarks/Bear-Statue/`, `pages/cedar-mountain-craig-co-local-guide/`, `pages/rotary-park/`, `pages/woodbury-park/`. `pages/things to do in vail colorado/index.html` is 42 words. That page is still linked from the Vail hub because the URL already exists. It is not a page another site would cite.

`scripts/page_queue.md` still says "Total remaining: 236" and still lists Bronco, Eagle, Einstein, Lady Doctor, the landmarks hub, Denver, and Vail as not templated. Its PNET title is the pre-rewrite title. The queue was left as-is. Do not treat it as the current inventory.

### No about, author, or contact page

There is no `about/`, `author/`, or `contact/` directory. Twenty-two pages include `mailto:testedprofit@gmail.com`. Nothing on the site says who writes the guides, how a correction should be sent, or why a newspaper or a city art program should trust the page. A real about page is a new URL. It is not the homepage, and this pass does not add it.

### Internal links and two Vail URLs

Vail has two activity URLs:

- `https://testedprofit.com/pages/things-to-do-in-vail-colorado/` — title "Things to Do in Vail, Colorado | Official 2026 Visitor Guide". That word "Official" is the page's own title. It is not a Town of Vail publication.
- `https://testedprofit.com/pages/things%20to%20do%20in%20vail%20colorado/` — title "Vail on a Budget | Free & Local Guide 2026". The directory name contains spaces. The page is thin.

Both stay. They are different URLs with different canonicals, so they split any links they receive. The Vail hub links both and says the activity pages are not town publications.

Finished guides also use older link text on some related-link lists. Hubs should use the live title of each guide. The Denver hub already does this. The Vail hub now does too.

### Sitemap, robots, and canonicals

`robots.txt` allows `/`, disallows `/preview/`, and points `Sitemap:` at `https://testedprofit.com/sitemap.xml`. The note about Shopify-style query parameters is intentional: those URLs stay crawlable because each public page declares a canonical. That is not a defect in the file.

`sitemap.xml` has 272 URLs. After unescaping `&amp;` and decoding `%20`, 16 HTML files are absent. The content ones worth knowing about are `CO/Landmarks/Bear-Statue/index.html`, `pages/woodbury-park/index.html`, `pages/rotary-park/index.html`, `pages/cedar-mountain-craig-co-local-guide/index.html`, and `pages/earnapp-definitive-review-philippines/index.html`. The rest are `404.html`, a Yandex verification file, `tokenomics/`, `espanol/`, `blogs/news/`, and app or archive paths this project does not edit (`pages/genesis/`, Crypto Tax-Loss Harvester, Freelance Rate Fairness Checker, conservation-fund contract frontends).

Canonicals that exist use `https://testedprofit.com`. No `http://` canonicals turned up. Duplicate titles: none. Pages under `pages/` that still lack a description, a canonical, or a single H1 include `pages/honey-rock-dogs-boarding-kennels/`, `pages/Woodbury Park/`, `pages/torii-square-park-westminster/`, `pages/martin-luther-king-memorial/`, `pages/Oakhurst Park II/`, and `pages/rocky-flats-national-wildlife-refuge-south-entrance/` (no description). `pages/genesis/index.html` has two H1s. App screens `pages/nfts/`, `pages/Security Lab/`, `pages/algoflow/`, and `pages/PNET/pnetleaderboard/` have no H1. Those app screens stay untouched.

### The live site is behind main

`.github/workflows/static.yml` ("Deploy static content to Pages") runs on `push` to `main` and on `workflow_dispatch`. It has no path filter. Permissions are `contents: read`, `pages: write`, and `id-token: write`. Concurrency group `pages` does not cancel an in-progress deploy. Nothing in that file explains why pushes to `main` since `4379e95` produced no workflow run. The file was not edited.

Do not send backlink pitches until the live URL shows the page you are pitching. A city editor who opens a stale title will not add the link.

## Ranked pitches

Pitch the guide as a companion to a page that already owns the subject. Ask for a normal link. Do not ask Wikipedia to cite testedprofit.com. Do not offer a photo the site does not have rights to upload.

1. **Town of Vail, Art in Vail.** [Program page](https://www.vail.gov/government/artinvail/) and [collection page](https://www.vail.gov/government/art-in-vail/collection). Pitch the Einstein bench guide as a visitor companion: where it stands, the 2014 donation, and what is not known about the cast. Ask whether a collection or map entry for this work, if they keep one, can link the guide. Do not claim the current town pages name Einstein. The indexed program text says the program was adopted in 1992 and describes more than 70 works. Vail Daily in 2014 said more than 40. Keep those counts on the pages that printed them. A direct fetch of vail.gov from this environment returned an Akamai 403, so the pitch should be checked in a browser before it is sent.

2. **Discover Vail.** [Einstein Bench](https://discovervail.com/vail-stories-einstein-bench/) and [Art in Public Places](https://discovervail.com/things-to-do/art-in-public-spaces/). The bench story already tells people to sit with the sculpture and says the collection has more than 40 works. The art page says more than 70 pieces and names a bronze Einstein on a bench. Pitch the practical how-to-find page: 183 Gore Creek Drive, the hotel pin, and the statement that the studio page does not identify the Vail cast.

3. **Gary Lee Price.** [Einstein studio page](https://garyleeprice.com/product/einstein/). Pitch an "on view in Vail" link. The page lists 2005 bronze editions at 52 inches and 18 inches. It does not say which edition is on Gore Creek Drive. Do not copy the prices onto the pitch or the guide.

4. **Vail Daily.** ["What's the future for 'Einstein'?", 9 October 2014](https://www.vaildaily.com/news/whats-the-future-for-einstein/). This is the primary news record: Sitzmark Vail, Bob and Helen Fritch, Gary Lee Price, the Great Contributors series, and Molly Eppard's statement that the bench would stay in front of the Sitzmark. Pitch a present-tense visitor guide that cites the article. Ask them to link the guide. Ask them to keep their own article as the source of the donation.

5. **Sitzmark Vail.** [sitzmarkvail.com](https://sitzmarkvail.com/). The hotel site publishes 183 Gore Creek Drive, Vail, Colorado 81657. Vail Daily places the bench in front of the hotel. Pitch a short public-art note. A hotel site often will not link out. It is still the right local ask.

6. **Atlas Obscura or a Roadside America-style listing, only if one does not already exist.** Submit the 2014 donation, the artist, the series name, and the hotel-front location. Do not submit the studio dimensions as the size of the Vail cast. Do not invent a photograph. If a listing exists, send a correction instead of a second listing.

7. **Bronco Buster.** [Denver Public Art, Broncho Buster](https://denverpublicart.org/public-arts/broncho-buster/) and [Civic Center Conservancy, Art in the Park](https://civiccenterpark.org/visit/public-art/). Pitch the Civic Center visitor guide as a companion. Use each site's own spelling. Denver Public Art uses "Broncho". The conservancy page uses "Bronco Buster".

8. **Lady Doctor.** [RTD, Honoring Dr. Justina Ford, 8 February 2022](https://www.rtd-denver.com/community/news/honoring-dr-justina-ford-colorados-first-licensed-black-woman-physician), [RTD art at rail stations](https://www.rtd-denver.com/art-n-transit/rail-stations), and [Colorado Encyclopedia, Justina Ford](https://coloradoencyclopedia.org/article/justina-ford). Pitch the guide to the 1998 Jess DuBois bronze at the 30th and Downing station plaza. Do not mix it up with the later Aurora Highlands statue of Dr. Ford.

9. **Newsboy in Golden.** [Visit Golden public art walks](https://www.visitgolden.com/things-to-do/arts-entertainment/art-museums-galleries-public-art-walks/), the [2018 public art brochure](https://assets.simpleviewinc.com/simpleview/image/upload/v1/clients/goldenco/PublicArtBrochure2018_47c3b4c6-84b0-4443-bb9b-2a7a6fb942df.pdf) (James Muir, northwest corner of the Washington Avenue bridge, placed 5 December 2003), [City of Golden, The Newsboy](https://www.cityofgolden.gov/business_detail_T31_R46.php), and [CPR News, 27 May 2024](https://www.cpr.org/2024/05/27/why-are-there-so-many-bronze-statues-in-golden/). Pitch the Golden installation. [James Muir's Newsboy page](https://jamesmuir.com/the-newsboy-life-size-bronze-sculpture-allegory-james-muir-2/) does not name Golden in the indexed text. Ask the studio whether that page is the Golden cast before linking the two. Do not pitch the Town of Cary newsboy or London's Three Printers.

10. **Westminster Sensory Park.** The guide already cites the City of Westminster parks inventory, Colorado Community Media, and 5280. Pitch the parks department from those citations. Do not send the pitch to Westminster Station Park and Nature Playground. That is a different park.

11. **Cowboy in Pajamas and Botero's Man and Woman.** The guides already name seanomeallie.com, Denver Arts and Venues, and Visit Denver. Confirm the exact URL on each site before sending. Pitch the installation the guide already describes (1725 Champa St for the cowboy; the Performing Arts galleria for Botero). Do not open a new statue page to support the pitch.

12. **Lakewood eagle.** Google Maps already lists "Eagle statue" at 1400 Denver West-Marriott Blvd. Sculptor, date, material, and size are not posted. Do not pitch an artist site. Do not pitch Wikipedia.

13. **Gillette rock paper scissors.** [Roadside America already lists it](https://www.roadsideamerica.com/tip/35294). Pitch a correction only where the on-site guide has a verified fact that listing lacks. Look for the City of Gillette Avenues of Art page and pitch that. Do not file a second roadside listing.

14. **Wikipedia and Wikimedia Commons.** Do not pitch testedprofit.com as a citation. The sources that can be cited are Vail Daily, Discover Vail, the town, RTD, Colorado Encyclopedia, Denver Public Art, and the Visit Golden brochure. Do not upload a photograph to Commons without a release from the photographer. Do not invent an image.

## Order of work after this pull request

Wait until GitHub Pages is actually serving `main`. Then add follow links to the source lines on the finished guides, one page per pull request. Then add an about and contact URL that is not the homepage. Then decide what to do with the thin space-URL Vail page without deleting the URL. Leave the deploy workflow alone unless the owner asks for an edit.
