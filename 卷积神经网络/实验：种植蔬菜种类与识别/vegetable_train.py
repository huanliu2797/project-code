## 导入库
import torch.nn.functional as F
import torch.optim as optim
import torch
import torch.nn as nn
import torch.nn.parallel

import torch.optim
import torch.utils.data
import torch.utils.data.distributed
import torchvision.transforms as transforms
import torchvision.datasets as datasets
from torch.autograd import Variable
# 设置超参数
#每次的个数
BATCH_SIZE = 20
#迭代次数
EPOCHS = 10
#采用cpu还是gpu进行计算
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
# 数据预处理

transform = transforms.Compose([
    transforms.Resize([150,150]),
    # transforms.RandomVerticalFlip(),
    # transforms.RandomCrop(50),
    # transforms.RandomResizedCrop(150),
    # transforms.ColorJitter(brightness=0.5, contrast=0.5, hue=0.5),
    transforms.ToTensor(),
    transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])
])
# 读取数据

dataset_train = datasets.ImageFolder('E:\pythonProject\code\course\项目实战：种植蔬菜种类识别与应用\基础实验\datasets\\train', transform)

print(dataset_train.imgs)

# 对应文件夹的label

print(dataset_train.class_to_idx)

dataset_test = datasets.ImageFolder('E:\pythonProject\code\course\项目实战：种植蔬菜种类识别与应用\基础实验\datasets\\validation', transform)

# 对应文件夹的label

print(dataset_test.class_to_idx)

# 导入数据

train_loader = torch.utils.data.DataLoader(dataset_train, batch_size=BATCH_SIZE, shuffle=True)

test_loader = torch.utils.data.DataLoader(dataset_test, batch_size=BATCH_SIZE, shuffle=False)


# 定义网络
class ConvNet(nn.Module):
    def __init__(self):
        super(ConvNet, self).__init__()
        self.conv1 = nn.Conv2d(3, 32, 3)
        self.max_pool1 = nn.MaxPool2d(2)
        self.conv2 = nn.Conv2d(32, 64, 3)
        self.max_pool2 = nn.MaxPool2d(2)
        self.conv3 = nn.Conv2d(64, 64, 3)
        self.conv4 = nn.Conv2d(64, 64, 3)
        self.max_pool3 = nn.MaxPool2d(2)
        self.conv5 = nn.Conv2d(64, 128, 3)
        self.conv6 = nn.Conv2d(128, 128, 3)
        self.max_pool4 = nn.MaxPool2d(2)
        self.fc1 = nn.Linear(4608, 512)
        self.fc2 = nn.Linear(512, 3)

    def forward(self, x):
        in_size = x.size(0)
        x = self.conv1(x)
        x = F.relu(x)
        x = self.max_pool1(x)
        x = self.conv2(x)
        x = F.relu(x)
        x = self.max_pool2(x)
        x = self.conv3(x)
        x = F.relu(x)
        x = self.conv4(x)
        x = F.relu(x)
        x = self.max_pool3(x)
        x = self.conv5(x)
        x = F.relu(x)
        x = self.conv6(x)
        x = F.relu(x)
        x = self.max_pool4(x)
        # 展开
        x = x.view(in_size, -1)
        x = self.fc1(x)
        x = F.relu(x)
        x = self.fc2(x)
        # x = torch.softmax(x)
        return x


modellr = 1e-4

# 实例化模型并且移动到GPU

model = ConvNet().to(DEVICE)

# 选择简单暴力的Adam优化器，学习率调低

optimizer = optim.Adam(model.parameters(), lr=modellr)
criterion = nn.CrossEntropyLoss()
def adjust_learning_rate(optimizer, epoch):
    """Sets the learning rate to the initial LR decayed by 10 every 30 epochs"""
    modellrnew = modellr * (0.1 ** (epoch // 5))
    # print("lr:", modellrnew)
    for param_group in optimizer.param_groups:
        param_group['lr'] = modellrnew


# 定义训练过程

def train(model, device, train_loader, optimizer, epoch):
    model.train()
    sum_loss = 0
    total_num = len(train_loader.dataset)
    # print(total_num, len(train_loader))
    for batch_idx, (data, target) in enumerate(train_loader):
        data, target = Variable(data).to(device), Variable(target).to(device)
        output = model(data)
        loss = criterion(output, target)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        print_loss = loss.data.item()
        sum_loss += print_loss
        if (batch_idx + 1) % 50 == 0:
            print('Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(
                epoch, (batch_idx + 1) * len(data), len(train_loader.dataset),
                       100. * (batch_idx + 1) / len(train_loader), loss.item()))
    ave_loss = sum_loss / len(train_loader)
    print('epoch:{},loss:{}'.format(epoch, ave_loss))


def val(model, device, test_loader):
    model.eval()
    test_loss = 0
    correct = 0
    total_num = len(test_loader.dataset)
    # print(total_num, len(test_loader))
    with torch.no_grad():
        for data, target in test_loader:
            data, target = Variable(data).to(device), Variable(target).to(device)
            output = model(data)
            loss = criterion(output, target)
            _, pred = torch.max(output.data, 1)
            correct += torch.sum(pred == target)
            print_loss = loss.data.item()
            test_loss += print_loss
        correct = correct.data.item()
        acc = correct / total_num
        avgloss = test_loss / len(test_loader)
        print('\nVal set: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)\n'.format(
            avgloss, correct, len(test_loader.dataset), 100 * acc))


# 训练

for epoch in range(1, EPOCHS + 1):
    adjust_learning_rate(optimizer, epoch)
    train(model, DEVICE, train_loader, optimizer, epoch)
    val(model, DEVICE, test_loader)
torch.save(model, 'model.pth')
