import torch.nn as nn
from torchvision import models

resnet_dict = {"ResNet18": models.resnet18, "ResNet34": models.resnet34,
               "ResNet50": models.resnet50, "ResNet101": models.resnet101,
               "ResNet152": models.resnet152}


class ResNet(nn.Module):
    def __init__(self, hash_bit, res_model="ResNet50"):
        super(ResNet, self).__init__()
        model_resnet = resnet_dict[res_model](pretrained=True)
        self.conv1 = model_resnet.conv1
        self.bn1 = model_resnet.bn1
        self.relu = model_resnet.relu
        self.maxpool = model_resnet.maxpool
        self.layer1 = model_resnet.layer1
        self.layer2 = model_resnet.layer2
        self.layer3 = model_resnet.layer3
        self.layer4 = model_resnet.layer4
        self.avgpool = model_resnet.avgpool
        self.feature_layers = nn.Sequential(self.conv1, self.bn1, self.relu, self.maxpool, self.layer1, self.layer2,
                                            self.layer3, self.layer4, self.avgpool)
        self.hash_layer = nn.Linear(model_resnet.fc.in_features, hash_bit)
        self.hash_layer.weight.data.normal_(0, 0.01)
        self.hash_layer.bias.data.fill_(0.0)

    def forward(self, x):
        x = self.feature_layers(x)
        x = x.view(x.size(0), -1)
        y = self.hash_layer(x)
        return y

    def adv_forward(self, x, alpha=1):
        x = self.feature_layers(x)
        x = x.view(x.size(0), -1)
        x = self.hash_layer(x)
        layer = nn.Tanh()
        y = layer(alpha * x)
        return y


# Vgg
vgg_dict = {"Vgg11": models.vgg11, "Vgg13": models.vgg13,
            "Vgg16": models.vgg16, "Vgg19": models.vgg19}


class Vgg(nn.Module):
    def __init__(self, hash_bit, vgg_model="Vgg16"):
        super(Vgg, self).__init__()
        model_vgg = vgg_dict[vgg_model](pretrained=True)
        self.features = model_vgg.features
        cl1 = nn.Linear(512 * 7 * 7, 4096)
        cl1.weight = model_vgg.classifier[0].weight
        cl1.bias = model_vgg.classifier[0].bias

        cl2 = nn.Linear(4096, 4096)
        cl2.weight = model_vgg.classifier[3].weight
        cl2.bias = model_vgg.classifier[3].bias

        self.hash_layer = nn.Sequential(
            cl1,
            nn.ReLU(inplace=True),
            nn.Dropout(),
            cl2,
            nn.ReLU(inplace=True),
            nn.Dropout(),
            nn.Linear(4096, hash_bit),
        )

    def forward(self, x):
        x = self.features(x)
        x = x.contiguous().view(x.size(0), 512 * 7 * 7)
        x = self.hash_layer(x)
        return x

    def adv_forward(self, x, alpha=1):
        x = self.features(x)
        x = x.contiguous().view(x.size(0), 512 * 7 * 7)
        x = self.hash_layer(x)
        layer = nn.Tanh()
        y = layer(alpha * x)
        return y
