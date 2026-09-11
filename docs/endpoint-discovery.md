# Endpoint discovery notes

These notes document the small, reproducible probe used to define the public API.

| Operation or route | Status | Package behavior |
| --- | --- | --- |
| `GetListingRental` / `searchRentals` | Verified in visible Chrome | Included |
| `RentalListingDetailsFederated` | Externally reported and fixture-tested | Included |
| `rentalByListingId` | Externally reported and fixture-tested | Included |
| `buildingByRentalListingId` | Externally reported and fixture-tested | Included |
| `getBuildingExpressByRentalListingId` | Externally reported and fixture-tested | Included |
| Sale search/detail operations | Not reproducibly identified | Excluded |
| `ShareToken` | Observed tracking mutation | Excluded |
| `/hdp/monolith` | Observed analytics route | Excluded |
| Rello and lead-generation calls | Externally reported | Excluded |

## Included operation

StreetEasy's visible rental search currently sends `POST https://api-v6.streeteasy.com/` with the GraphQL operation `GetListingRental($input: SearchRentalsInput!)`. The observed input supports rental status, area IDs, price bounds, bedroom bounds, pagination, and sorting. The response supplies a total count and listing edges with the fields parsed by this package.

The operation was observed from an ordinary visible Chrome session on a public rental search. A minimal headless probe received HTTP 403, while visible Chrome loaded the search and operation successfully. This is why the optional browser transport is explicitly headful.

### Rental details

The current open-source [`evandcoleman/streeteasy-api`](https://github.com/evandcoleman/streeteasy-api) project documents a second operation on the same GraphQL endpoint: `RentalListingDetailsFederated($listingID: ID!)`. Its query combines these read resolvers:

- `rentalByListingId`
- `buildingByRentalListingId`
- `getBuildingExpressByRentalListingId`
- `getRelloRentalById`
- `getRentalListingExpressById`

This package implements the first three, which provide the useful public listing, building, transit, and school data. The Rello call is a lead-generation CTA and the final express call only reports showcase state, so neither is included.

Online source comparison also exposed additional `SearchRentalsInput` filters: bathrooms, amenities, optional amenities, pets, and an availability date bound. These are now represented by `SearchFilters`.

The bundled area catalog contains 322 numeric identifiers from the same public client source and records its snapshot date. Friendly lookup is case-insensitive and remains overridable through direct `area_ids`.

## Excluded traffic

- `ShareToken` creates tracking/share tokens and is unrelated to listing retrieval.
- `/hdp/monolith` is analytics traffic and is unrelated to listing retrieval.
- Detail pages did not expose another stable, useful read operation during the probe.
- No reproducible sale-search or sale-detail GraphQL operation was found in the reviewed public code.

The package does not call those routes. It also does not include challenge solving, cookie extraction, fingerprint spoofing, account automation, or rate-limit bypass behavior.

## Stability and access

This is an undocumented website operation and may change without notice. StreetEasy's current robots file disallows several rental and API-style paths, and its terms restrict automated scraping without permission. Callers must assess and obtain the access they need. Keep requests small, cache results, and stop on access errors.

- [StreetEasy robots.txt](https://streeteasy.com/robots.txt)
- [StreetEasy advertiser terms](https://streeteasy.com/business/ad-terms-of-service/)
