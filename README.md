# STATUS - PyPI Download Metrics for SEMCL.ONE tools

A GitHub Pages dashboard that tracks download statistics for all SEMCL.ONE packages published on PyPI.

For setup and customization instructions, see [INSTRUCTIONS.md](INSTRUCTIONS.md).

## Tracked Packages

The dashboard tracks these SEMCL.ONE packages:

- **purl2src** - Downloads source code from Package URLs
- **binarysniffer** - Identifies hidden OSS components in binaries
- **osslili** - High-performance license detection
- **purl2notices** - Generates legal notices with licenses
- **ossnotices** - Simplified CLI for generating legal notices
- **upmex** - Universal package metadata extractor
- **src2purl** - Identifies package coordinates from source code
- **vulnq** - Multi-source vulnerability query tool
- **ospac** - Open Source Policy as Code engine
- **mcp-semclone** - MCP server for OSS compliance analysis
- **ossval** - Development cost savings from open source, via COCOMO II
- **ossbomer** - Profile-driven SBOM validation, conformance and license policy
- **suphm** - Supply chain health metrics and maintainer burnout signals

This list is maintained by hand and the dashboard is not: the page reads
`docs/data/stats.json` and renders whatever it finds. So a package can be
tracked and charted while missing from this list, which is what happened to
`ossnotices` and `ossval`. If you add to `PACKAGES` in `fetch_stats.py`, add it
here too.

## License

See [LICENSE](LICENSE) file for details.
