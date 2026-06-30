models and model-shelf.json should be in the same directory.
`provider-configs` - what is this, 

nr@Nachikeths-MacBook-Air ~ % ms init
Where should Model Shelf live? [./model-shelf]

it should be the root diestory when doing this

for example, of i type ~/

then it should create a folder called model-shelf and then 
inside that,
gguf
mlx
safetensors
and i dont know why you what to store provider-configs but maybe think and explain about that

should be like this:
model-shelf/
├── gguf/
│   └── Qwen/
│       └── Qwen3-14B-GGUF/
│           └── Qwen3-14B-Q4_K_M.gguf
├── mlx/
│   └── mlx-community/
│       └── Qwen3-14B-4bit/
└── safetensors/
    └── Qwen/
        └── Qwen3-14B/


``` bash
nr@Nachikeths-MacBook-Air model-shelf % ms search gemma4
No models found.
```
the hugging face search is not working...


Direct Install
Dry run:

ms install qwen --format gguf --source
Actually run the install:

ms install qwen --format gguf --source --yes
Use a different manifest command:

ms install qwen --format gguf --source --command git_lfs --yes


need to make this more secific to the model or the hf url.
