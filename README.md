To get the logs:
`k logs $(k get pods | grep mapping-deploy | cut -d ' ' -f1) mapping-consumer-task --follow`
`k logs $(k get pods | grep mapping-deploy | grep Running | cut -d ' ' -f1) mapping-consumer-task --follow` 