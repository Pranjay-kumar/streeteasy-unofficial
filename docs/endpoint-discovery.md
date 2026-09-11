# Endpoint discovery notes

These notes document the small, reproducible probe used to define the public API.

## Included operation

StreetEasy's visible rental search currently sends `POST https://api-v6.streeteasy.com/` with the GraphQL operation `GetListingRental($input: SearchRentalsInput!)`. The observed input supports rental status, area IDs, price bounds, bedroom bounds, pagination, and sorting. The response supplies a total count and listing edges with the fields parsed by this package.

The operation was observed from an ordinary visible Chrome session on a public rental search. A minimal headless probe received HTTP 403, while visible Chrome loaded the search and operation successfully. This is why the optional browser transport is explicitly headful.

## Excluded traffic

- `ShareToken` creates tracking/share tokens and is unrelated to listing retrieval.
- `/hdp/monolith` is analytics traffic and is unrelated to listing retrieval.
- Detail pages did not expose another stable, useful read operation during the probe.

The package does not call those routes. It also does not include challenge solving, cookie extraction, fingerprint spoofing, account automation, or rate-limit bypass behavior.

## Stability and access

This is an undocumented website operation and may change without notice. StreetEasy's current robots file disallows several rental and API-style paths, and its terms restrict automated scraping without permission. Callers must assess and obtain the access they need. Keep requests small, cache results, and stop on access errors.

- [StreetEasy robots.txt](https://streeteasy.com/robots.txt)
- [StreetEasy advertiser terms](https://streeteasy.com/business/ad-terms-of-service/)
