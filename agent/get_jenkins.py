import jenkins
import json
from datetime import datetime
jenkins_url = 'https://jenkins-approval.aijidou.com'
username = 'stevenwang'
password = 'Babyboom1001!'
server = jenkins.Jenkins(jenkins_url, username=username, password=password)

jobs = server.get_all_jobs()

def get_jenkins_history():
    job_names = [job['name'] for job in jobs]
    build_info = []
    for job_name in job_names:
        builds = server.get_job_info(job_name)['builds']
        for build in builds:
            build_details = server.get_build_info(job_name, build['number'])
            timestamp = build_details['timestamp']
            formatted_time = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
            build_info.append((job_name, build['number'], timestamp, formatted_time))

    build_info.sort(key=lambda x: x[2], reverse=True)
    build_info = build_info[:10]

    # 移除原始时间戳并构建数据字典
    data = {
        'latest_builds': [
            {
                'job_name': job,
                'build_number': number,
                'build_time': formatted_time
            }
            for job, number, _, formatted_time in build_info
        ]
    }
    print(data)
    #return data

get_jenkins_history()