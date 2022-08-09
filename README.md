To get the logs:
`k logs $(k get pods | grep mapping-deploy | cut -d ' ' -f1) mapping-consumer-task --follow`
`k logs $(k get pods | grep mapping-deploy | grep Running | cut -d ' ' -f1) mapping-consumer-task --follow`

## Mapping API
To call the API:

```bash
curl -X POST \
    $(minikube service mapping-service --url)/textmap \
    -H "Content-Type: application/json"  \
    -d '{
        "source_urls": [
            "https://www.youtube.com/watch?v=LJ4W1g-6JiY",
            "https://www.youtube.com/watch?v=pXswr3XmDw8",
            "https://www.youtube.com/watch?v=DHjqpvDnNGE"
        ],
        "user_id": "a_user_id",
        "limit": 50
    }' \
    | python -m json.tool \
    | python -c "import sys, json; print(json.load(sys.stdin)['job_id'])" \
    | tee _temp.txt \
&& \
export SEQ_ID=$(cat _temp.txt) \
&& echo sequence_id=$SEQ_ID
```

To get the results:
```shell
export SEQ_ID=$(cat _temp.txt) && \
curl \
    -X GET \
    "$(minikube service mapping-service --url)/textmap/sequence_id/$SEQ_ID?include_clustering=false" \
    | python -m json.tool
```



To stop the job:
```shell
export SEQ_ID=$(cat _temp.txt) && \
curl -X PUT \
    $(minikube service mapping-service --url)/textmap \
    -d "{
        \"sequence_id\": \"$SEQ_ID\"
    }"
```