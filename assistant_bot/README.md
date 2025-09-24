# A demo assistant bot

you need setup the environment key via command 'export ANTHROPIC_API_KEY=XXXXXX'. You can generate this key on the website: https://console.anthropic.com/settings/keys

# Run within docker

you can build a docker container with command
`docker build . -t bot`
and run it with command
`docker run --rm -e ANTHROPIC_API_KEY=xxx -v /path/mount:/mnt -it bot`
the bot will read/write within dir `/mnt`. If you want to check the result after terminated it, make sure you pass the path correctly.
