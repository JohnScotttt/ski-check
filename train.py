import argparse
import math
import os
from matplotlib import pyplot as plt
import numpy as np

import torch
import torch.nn as nn
from torch.autograd import Variable
from torch.utils.data import DataLoader
from torchvision import models, transforms

from dataloader import mnist_loader as ml


def train():
    os.makedirs('./output', exist_ok=True)
    if True: #not os.path.exists('output/total.txt'):
        ml.image_list(args.datapath, 'output/total.txt')
        ml.shuffle_split('output/total.txt', 'output/train.txt', 'output/val.txt')

    train_data = ml.MyDataset(txt='output/train.txt', transform=transforms.Compose([transforms.ToTensor(),transforms.RandomHorizontalFlip()]))
    # train_data = ml.MyDataset(txt='output/train.txt', transform=transforms.ToTensor())
    val_data = ml.MyDataset(txt='output/val.txt', transform=transforms.Compose([transforms.ToTensor(),transforms.RandomHorizontalFlip()]))
    # val_data = ml.MyDataset(txt='output/val.txt', transform=transforms.ToTensor())
    train_loader = DataLoader(dataset=train_data, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(dataset=val_data, batch_size=args.batch_size)

    model = models.resnet152(num_classes=3)
    # model.load_state_dict(torch.load('output/params_50.pth'))

    if args.cuda:
        print('training with cuda')
        model.cuda()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01, weight_decay=1e-3)
    scheduler = torch.optim.lr_scheduler.MultiStepLR(optimizer, [30, 60], 0.1)
    loss_func = nn.CrossEntropyLoss()

    for epoch in range(args.epochs):
        # training-----------------------------------
        model.train()
        train_loss = 0
        train_acc = 0
        for batch, (batch_x, batch_y) in enumerate(train_loader):
            if args.cuda:
                batch_x, batch_y = Variable(batch_x.cuda()), Variable(batch_y.cuda())
            else:
                batch_x, batch_y = Variable(batch_x), Variable(batch_y)
            out = model(batch_x)
            loss = loss_func(out, batch_y)
            train_loss += loss.item()
            pred = torch.max(out, 1)[1]
            train_correct = (pred == batch_y).sum()
            train_acc += train_correct.item()
            print('epoch: %2d/%d batch %3d/%d  Train Loss: %.3f, Acc: %.3f'
                  % (epoch + 1, args.epochs, batch, math.ceil(len(train_data) / args.batch_size),
                     loss.item(), train_correct.item() / len(batch_x)))

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        scheduler.step()  # 更新learning rate
        print('Train Loss: %.6f, Acc: %.3f' % (train_loss / (math.ceil(len(train_data)/args.batch_size)),
                                               train_acc / (len(train_data))))
        losslist.append(train_loss / (math.ceil(len(train_data)/args.batch_size)))
        acclist.append(train_acc / (len(train_data)))
        # evaluation--------------------------------
        model.eval()
        eval_loss = 0
        eval_acc = 0
        for batch_x, batch_y in val_loader:
            if args.cuda:
                batch_x, batch_y = Variable(batch_x.cuda()), Variable(batch_y.cuda())
            else:
                batch_x, batch_y = Variable(batch_x), Variable(batch_y)

            out = model(batch_x)
            loss = loss_func(out, batch_y)
            eval_loss += loss.item()
            pred = torch.max(out, 1)[1]
            num_correct = (pred == batch_y).sum()
            eval_acc += num_correct.item()
        print('Val Loss: %.6f, Acc: %.3f' % (eval_loss / (math.ceil(len(val_data)/args.batch_size)),
                                             eval_acc / (len(val_data))))
        # save model --------------------------------
        if (epoch + 1) % 1 == 0:
            # torch.save(model, 'output/model_' + str(epoch+1) + '.pth')
            torch.save(model.state_dict(), 'output/params_' + str(epoch + 1) + '.pth')
            #to_onnx(model, 3, 28, 28, 'params.onnx')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PyTorch MNIST Example')
    parser.add_argument('--datapath', required=True, help='data path')
    parser.add_argument('--batch_size', type=int, default=64, help='training batch size')
    parser.add_argument('--epochs', type=int, default=60, help='number of epochs to train')
    parser.add_argument('--use_cuda', default=True, help='using CUDA for training')

    args = parser.parse_args()
    args.cuda = args.use_cuda and torch.cuda.is_available()
    if args.cuda:
        torch.backends.cudnn.benchmark = True

    losslist=[]
    acclist=[]

    train()

    cost = np.array(losslist)
    acc = np.array(acclist)

    plt.ylabel('Accuracy rate / cost')
    plt.xlabel('iterations (per Epoch)')
    plt.title("Learning rate = 0.01")

    plt.plot(cost,label='Cost')
    plt.plot(acc,label='Accuracy rate')
    plt.legend()
    plt.show()
