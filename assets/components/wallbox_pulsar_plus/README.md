# Wallbox Pulsar Plus body

`wallbox_pulsar_plus_body.scad` is an original, dimensionally scaled model of
the North American Wallbox Pulsar Plus enclosure. Its overall envelope and
profile proportions are derived from Wallbox's 2021 technical datasheet. The
bottom power-entry aperture is based on the North American installation guide.

The model uses inches and the repository's component coordinate convention:
`x` is vertical, `y` is horizontal, and `z` projects away from the mounting
surface. The included STL is generated from the SCAD source with:

```sh
openscad -o wallbox_pulsar_plus_body.stl wallbox_pulsar_plus_body.scad
```

Sources:

- [Pulsar Plus technical datasheet](https://support.wallbox.com/wp-content/uploads/ht_kb/2021/02/Pulsar_Plus_Datasheet.pdf)
- [Pulsar Plus North America installation guide](https://support.wallbox.com/na/knowledge-base/pulsar-plus-na-ig/)
