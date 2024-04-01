#/bin/bash
echo 'Now start workspace.entrypoint.sh...'

network=$(docker network ls --filter name="github-action" --format {{.Name}})

if [ -z $network ]; then
    echo '"github-action" not found. will create.'
    docker network create github-action &1>/dev/null &2>&1
    if [ $?==0 ];then
        echo 'create network success.'
    else
        echo 'create network failed.'
        exit 1
    fi
else
    echo '"github-action" network existed.'
fi