# Research Project Proposal Key Area classification

Multi-class classify the Research Project Proposal description, contained within the fenced Markdown block:

```text
"$proposal"
```

Classify the above proposal into one or more of these three Key Areas:

- **SLIM** (Smart Region): Focuses on enhancing digital transformation and innovation within organizations and communities.
  By leveraging Digital Twin technology, Artificial Intelligence, and innovative learning environments, SLIM fosters adaptability, agility, and collaboration.
  The goal is to create digitally resilient ecosystems, optimize processes, and prepare professionals to thrive in a rapidly evolving technological landscape through public-private partnerships and field labs.
- **SCHOON** (Sustainable Energy and Environment): Focuses on reducing CO2 emissions and fostering a circular, sustainable economy.
  This multidimensional effort involves clean energy innovations, sustainable mobility solutions, environmentally-friendly construction practices, and efficient use of resources.
  Collaborating across education, business, and government, SCHOON promotes multidisciplinary projects that develop future-ready professionals and scalable, practical solutions for complex environmental challenges.
- **SOCIAAL**: Focuses on reducing socioeconomic health disparities by creating fairer health outcomes, improving social and economic positions, inclusive education and work, and fostering healthier living environments.
  Efforts involve collaboration among educators, researchers, and professionals to address issues like poverty, low literacy, and social exclusion, which negatively impact health.
  Through dialogue and practical initiatives, the aim is to develop sustainable solutions that empower individuals and communities.

Also provide a complete rationale for your decision, highlighting how key project objectives either align or do not align with each of the defined key areas.

Concretely, respond in the following JSON format:

```json
{
  "keyarea": {
    "schoon": true,
    "slim": true,
    "sociaal": true,
  },
  "rationale": "SCHOON ... SLIM ... SOCIAAL ..."
}
```

Where either of the keys under the `"keyarea"` dictionary (representing Key Areas, in lower case) can be `true` or `false` independently, to express the predicted clas(ses) (`true` meaning the research proposal does classify to that class).
