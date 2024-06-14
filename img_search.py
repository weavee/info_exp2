import os
import json
import jieba
import pickle
from collections import defaultdict

# 分词
def tokenize(text):
    return list(jieba.cut(text))

# 构建倒排索引
def build_inverted_index(root_folder_path):
    inverted_index = defaultdict(list)
    docs = []
    for folder_name in os.listdir(root_folder_path):
        folder_path = os.path.join(root_folder_path, folder_name)
        if os.path.isdir(folder_path):
            for filename in os.listdir(folder_path):
                if filename.endswith(".jpg"):
                    json_filename = filename.replace('.jpg', '_url.json')
                    json_path = os.path.join(folder_path, json_filename)

                    # 读取现有的 JSON 文件
                    with open(json_path, 'r', encoding='utf-8') as json_file:
                        data = json.load(json_file)
                        article_name = data.get('article_name', '')
                        description = data.get('description', '')
                        extract_info = data.get('extract_info', '')
                        url = data.get('src', '')

                        doc_id = len(docs)
                        docs.append({
                            'article_name': article_name,
                            'description': description,
                            'extract_info': extract_info,
                            'url': url
                        })

                        full_text = f"{article_name} {description} {extract_info}"
                        tokens = tokenize(full_text)
                        for token in tokens:
                            inverted_index[token].append(doc_id)

    return inverted_index, docs

# 保存和加载倒排索引
def save_inverted_index(index, filepath):
    with open(filepath, 'wb') as file:
        pickle.dump(index, file)

def load_inverted_index(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'rb') as file:
            return pickle.load(file)
    return None

# 读取文档
def read_docs(folder_path):
    docs = []
    for folder_name in os.listdir(folder_path):
        folder_path_full = os.path.join(folder_path, folder_name)
        if os.path.isdir(folder_path_full):
            for filename in os.listdir(folder_path_full):
                if filename.endswith(".jpg"):
                    json_filename = filename.replace('.jpg', '_url.json')
                    json_path = os.path.join(folder_path_full, json_filename)
                    with open(json_path, 'r', encoding='utf-8') as json_file:
                        data = json.load(json_file)
                        article_name = data.get('article_name', '')
                        description = data.get('description', '')
                        extract_info = data.get('extract_info', '')
                        url = data.get('src', '')
                        docs.append({
                            'article_name': article_name,
                            'description': description,
                            'extract_info': extract_info,
                            'url': url
                        })
    return docs

# 构建文档向量
def build_document_vectors(words, inverted_index):
    document_vectors = defaultdict(lambda: defaultdict(int))
    for word in words:
        for doc_id in inverted_index.get(word, []):
            document_vectors[doc_id][word] += 1
    return document_vectors

# 排序文档
def rank_and_score_documents(query_vector, document_vectors):
    scores = {}
    for doc_id, doc_vector in document_vectors.items():
        score = sum(query_vector[word] * doc_vector.get(word, 0) for word in query_vector)
        scores[doc_id] = score
    sorted_docs = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return sorted_docs

# 中文分词
def chinese_word_segmentation(query, stop_words):
    words = tokenize(query)
    return [word for word in words if word not in stop_words]

# 加载停用词
def load_stop_words(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        stop_words = set(file.read().split())
    return stop_words


# 保存和加载查询评分
def save_scores(scores, filepath):
    with open(filepath, 'wb') as file:
        pickle.dump(scores, file)


def load_scores(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'rb') as file:
            return pickle.load(file)
    return {}


# 主函数和命令行接口
def main():
    ######################################
    ##  1. 加载倒排索引文件
    folder_path = 'img_data_set'
    stop_words = load_stop_words('stop_words.txt')
    index_file_path = 'img_data_set/inverted_index.pickle'
    scores_file_path = 'img_data_set/query_scores.pickle'

    document_store = read_docs(folder_path)
    inverted_index = load_inverted_index(index_file_path)
    if inverted_index is None:
        inverted_index, docs = build_inverted_index(folder_path)
        save_inverted_index(inverted_index, index_file_path)

    ######################################
    ##  2. 加载查询结果评分数据
    query_scores = load_scores(scores_file_path)  # 初始化查询评分数据

    ######################################
    ##  3. 不断处理query输入，
    ##     1 先构建查询向量，2 再据此计算文档向量，3 然后结合评分计算相似度，4 打印结果，5 评分，6 保存评分
    while True:
        # 1 构建query向量
        query = input("请输入查询内容（输入'exit'退出）：")
        if query == 'exit':
            break
        words = chinese_word_segmentation(query, stop_words)
        query_vector = {word: 1 for word in words}
        query_id = query
        print(f'查询向量为：{query_vector}')

        # 2 根据 query和倒排索引 构建 文档向量
        document_vectors = build_document_vectors(words, inverted_index)

        # 3 计算文档与query的相关度 并据此排序文档
        ranked_docs_with_scores = rank_and_score_documents(query_vector, document_vectors)

        # 4 打印查询结果及相关度
        if not ranked_docs_with_scores:
            print("没有找到相关的文档。")
        else:
            for i, (doc_id, score) in enumerate(ranked_docs_with_scores):
                doc = document_store[doc_id]
                print(f"搜索结果: {i+1}\n标题: {doc['article_name']}\n描述: {doc['description']}\n提取信息: {doc['extract_info']}\n相关度: {score:.4f}\nURL: {doc['url']}\n")

    # 保存评分数据
    save_scores(query_scores, scores_file_path)


if __name__ == '__main__':
    main()
