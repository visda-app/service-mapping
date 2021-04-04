curl \
    localhost:5001/textmap \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{
        "youtube_video_id": "oieNTzEeeX0"
    }'

curl localhost:5001/textmap/sequence_id/2e14bcab-c66b-4fef-bb39-628ed847e12c



# export visda_url=https://visda.app
# export visda_url=$(minikube service web-proxy-service --url)
# export visda_url=localhost:5001

curl -X POST \
    $visda_url/textmap \
    -H "Content-Type: application/json"  \
    -d '{
        "youtube_video_id": "oieNTzEeeX0"
    }' \
    | python -m json.tool \
    | python -c "import sys, json; print(json.load(sys.stdin)['job_id'])" \
    | tee _temp.txt
export SEQ_ID=$(cat _temp.txt)
echo sequence_id=$SEQ_ID
curl -X GET "$visda_url/textmap/sequence_id/$SEQ_ID" \
    | python -m json.tool
