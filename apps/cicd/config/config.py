jenkins_auths = {
    "dev": {
        "url": "https://jenkins-dev.aijidou.com",
        "username": "jenkins",
        "password": "Jidou1234",
        "credentialsId": "c803b1af-d23c-4c07-b81e-2469a3164abb"
    },

    "test": {
        "url": "https://jenkins-test.aijidou.com",
        "username": "jenkins",
        "password": "Jidou1234",
        "credentialsId": "c803b1af-d23c-4c07-b81e-2469a3164abb"
    },

    "approval": {
        "url": "https://jenkins-approval.aijidou.com",
        "username": "jenkins",
        "password": "Jidou1234",
        "credentialsId": "c803b1af-d23c-4c07-b81e-2469a3164abb"
    },
}

# 不同集群的配置信息, 用于确认部署到哪个集群中
cluster_map = {
    "jdocloud": {
        "kube_config": {
            "dev": "/root/.kube_jdo_dev_new/config",
            "test": "/root/.kube_jdo_test_new/config",
            "approval": "/root/.kube_jdo-and-oem-cloud-approval-cluster/config"
        },
        "jump_server": {
            "approval": "122.112.217.185",
            "live": "121.36.76.149"
        },
        "image_namespace":{
            "dev": "jdo-dev",
            "test": "jdo-test",
            "approval": "jdocloud"
        }
    },

    "hcp3": {
        "kube_config": {
            "approval": "/root/.kube_hcp3-jdo-k8s-approval/config",
            "live": "/root/.kube_hcp3-jdo-k8s-live/config"
        },
        "jump_server": {
            "approval": "49.4.8.222",
            "live": "不知道"
        },
        "image_namespace":{
            "dev": "hcp3-dev",
            "test": "hcp3-test",
            "approval": "hcp3-approval"
        }
    },

    "asterix": {
        "kube_config": {
            "approval": "/root/.kube_asterix-k8s-approval/config",
            "live": "/root/.kube_asterix-k8s-live/config"
        },
        "jump_server": {
            "approval": "49.4.8.222",
            "live": "不知道"
        },
        "image_namespace":{
            "dev": "asterix-dev",
            "test": "asterix-test",
            "approval": "asterix-approval"
        }
    }
}




base_image = {
    "jdk8": "hub-sh.aijidou.com/base/openjdk:8-jdk-slim-stretch",
    "jdk11": "hub-sh.aijidou.com/base/openjdk:11.0.8-jdk-slim",
    "jdk17": "hub-sh.aijidou.com/base/openjdk:22-ea-17-jdk-slim"
}