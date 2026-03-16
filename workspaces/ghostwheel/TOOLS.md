# Peer Interaction

To discover a peer's skills: `http_request GET http://aya:3200/`
To invoke a peer's skill: `http_request POST http://aya:3200/skills/report-bug {"summary":"..."}`

To discover Alastair's skills: `http_request GET http://alastair:3300/`
To invoke Alastair's skill: `http_request POST http://alastair:3300/skills/{name} {...}`
