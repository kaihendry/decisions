SITE := site
PORT := 8000

.PHONY: build clean view deploy

build:
	./build.py $(SITE)

clean:
	rm -rf $(SITE)

view: build
	@echo "http://localhost:$(PORT)/"
	@uv run python -m http.server $(PORT) --directory $(SITE) --bind 127.0.0.1

# Needs `npx wrangler@4 login` once. Publishes to https://decisions.dabase.com/
# Not `cf deploy`: as of cf 0.5.0 that needs an undocumented cloudflare.config.ts.
deploy: build
	npx --yes wrangler@4 deploy
