I built a small REST API for a fictional home brand, Lumo Living, that writes Instagram captions in English, German and Spanish.

The interesting part is that the brand guide does the steering. The service splits the guide into numbered rules, retrieves the ones that matter for each request, and returns exactly which rules it used. Then it checks every caption in code: word count, emojis, hashtags, forbidden claims. Anything that fails goes back to the model with the broken rules listed.

It also says no. Ask it to claim a diffuser "cures insomnia" and it refuses, names rule 3.1 and suggests a compliant angle. A second endpoint scores any caption against the guide.

Biggest lesson: don't trust the model to police itself. Let it write, then verify with plain code.

Built with FastAPI, Claude as my coding assistant, and a swappable Groq, Gemini or Ollama backend.
