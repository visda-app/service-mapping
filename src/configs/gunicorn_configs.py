import multiprocessing

bind = ":5001"
reload = "True"
# errorlog = '-'
# loglevel = 'info'
accesslog = '-'
timeout = 3600
access_log_format = (
    '%(h)s %(l)s %(u)s %(t)s '
    '"%(r)s" %(s)s %(b)s '
    '"%(f)s" "%(a)s"'
)
# access_log_format = '%(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
workers = multiprocessing.cpu_count() * 2 + 1
