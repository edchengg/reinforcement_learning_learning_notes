import numpy as np
import torch
from torch.autograd import Variable
from moleskin import Moleskin

M = Moleskin()

size = [2, 2]
n = 5

# show case scatter method on tensors
input = torch.FloatTensor(*size + [n]).zero_()
mask = torch.LongTensor(np.ones(size, dtype=np.int)).unsqueeze(dim=2).expand_as(input)
print(mask)
input.scatter_(-1, mask, n)
print(input)

# Now test scatter method on variables
input = Variable(torch.FloatTensor(*size).zero_().unsqueeze(dim=2).expand(*size, n))
mask = Variable(torch.LongTensor(np.ones(size, dtype=np.int)).unsqueeze(dim=2).expand_as(input))
source = 5 * Variable(torch.ones(input.size()), requires_grad=True)
print(mask)
output = input.scatter(-1, mask, source)
print(output)

loss = output.sum()
M.debug(source.grad)
loss.backward()
M.debug(source.grad),
assert source.grad is None, "source should not receive grad."
