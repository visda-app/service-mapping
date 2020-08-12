export MAPPING_URL=$(minikube service $(kubectl get service | grep "mapping.*proxy" | cut -d " " -f1) --url)
echo $MAPPING_URL
curl \
   -X GET \
   "$MAPPING_URL/job?sequence_id=seq-id-ep1-01-1"


curl \
   -X GET \
   "127.0.0.1:5001/job?sequence_id=seq-id-ep1-01-1"
