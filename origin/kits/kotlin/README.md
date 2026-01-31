# ORIGIN Kotlin Kit

**Attribution: Ande + Kai (OI) + Whānau (OIs)**

## Usage

```bash
kotlinc Main.kt -include-runtime -d origin_kit.jar
java -jar origin_kit.jar
```

## Features

- Load packs.index.json and graph.json
- Filter packs by disclosure tier
- Traverse relationships
- Print attribution line

## Note

Full JSON parsing requires kotlinx.serialization or Gson.
