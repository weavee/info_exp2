import os
import json
import jieba
import pickle
import math
from collections import defaultdict

############################################
# 人工评分相关部分
############################################
# 记录所有查询及其对应的所有文档打分的字典
class QueryScore:
    def __init__(self, score_dict=None):
        # 使用 typing 模块来指定类型
        from typing import Dict
        if score_dict is None:
            score_dict = {}
        self.scores: Dict[str, Dict[str, float]] = score_dict

    def add_score(self, query_id, doc_id, score):
        if query_id not in self.scores:
            self.scores[query_id] = {}
        if doc_id not in self.scores[query_id]:
            self.scores[query_id][doc_id] = score
        else:
            self.scores[query_id][doc_id] = score

    def get_score(self, query_id, doc_id):
        # 返回查询和文档的分数，如果不存在则返回 0
        return self.scores.get(query_id, {}).get(doc_id, 0)
    
def save_scores(scores, file_path):
    with open(file_path, 'wb') as file:
        pickle.dump(scores, file)

def load_scores(file_path):
    try:
        with open(file_path, 'rb') as file:
            return QueryScore(pickle.load(file))
    except FileNotFoundError:
        return QueryScore()


############################################
# 倒排索引构建相关
############################################
# 加载数据集
def read_docs():
    document_store = {}
    directory = 'data_set'

    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if 'Title' in data:
                    # 使用Title作为键，其余部分作为值添加到document_store字典中
                    document_store[data['Title']] = {key: value for key, value in data.items() if key != 'Title'}
                else:
                    print(f"Warning: '{filename}' does not contain a 'Title' key.")
    return document_store

# 构建和管理倒排索引
class InvertedIndex:
    def __init__(self, index_dict= {}):
        self.index = index_dict
    
    def add_document(self, doc_id, words):
        for word in words:
            if word not in self.index:
                self.index[word] = []
            if doc_id not in self.index[word]:
                self.index[word].append(doc_id)
    
    def get_documents(self, word):
        return self.index.get(word, [])
    
    def __str__(self) -> str:
        s = ''
        i = 0
        for word, docs in self.index.items():
            s += f'{word}: {docs}\n'
            i += 1
            if i > 10: break
        return s

# 加载停用词
def load_stop_words(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        stop_words = set([line.strip() for line in file.readlines()])
    return stop_words

# 使用jieba进行中文分词，并过滤掉停用词
def chinese_word_segmentation(text, stop_words):
    words = [word for word in jieba.cut(text, cut_all=False) if (word not in stop_words) and (word != ' ')]
    return words

# 构建倒排索引并保存到文件
def build_and_save_inverted_index(documents, index_file_path, stop_words):
    inverted_index = InvertedIndex()
    for doc_title, doc in documents.items():
        words = chinese_word_segmentation(doc['Content'], stop_words)
        inverted_index.add_document(doc_title, words)
    with open(index_file_path, 'wb') as file:
        pickle.dump(inverted_index.index, file)
    return inverted_index

# 从文件加载倒排索引
def load_inverted_index(index_file_path):
    try:
        with open(index_file_path, 'rb') as file:
            return InvertedIndex(pickle.load(file))
    except FileNotFoundError:
        print("倒排索引文件未找到，将创建新的倒排索引。")
        return None

############################################
# 相似度计算相关
############################################
# 构建文档向量
def build_document_vectors(query_words, inverted_index: dict):
    document_vectors = defaultdict(lambda: defaultdict(int))
    for word in query_words:
        if word in inverted_index.keys():
            for doc_title in inverted_index[word]:
                document_vectors[doc_title][word] += 1
    return document_vectors

# 计算余弦相似度
def cosine_similarity(vec1, vec2):
    intersection = set(vec1.keys()) & set(vec2.keys())
    if not intersection:
        return 0
    dot_product = sum([vec1[word] * vec2[word] for word in intersection])
    norm_vec1 = math.sqrt(sum([val**2 for val in vec1.values()]))
    norm_vec2 = math.sqrt(sum([val**2 for val in vec2.values()]))
    return dot_product / (norm_vec1 * norm_vec2) if norm_vec1 and norm_vec2 else 0

#  计算相关度并排序文档：结合人工评分版本
def rank_and_score_documents(query_vector, document_vectors, query_id, query_scores, limit= 5):
    ranked_docs_with_scores = []
    for doc_id, doc_vector in document_vectors.items():
        score = 10 * cosine_similarity(query_vector, doc_vector)
        # 人工评分的平均值
        average_score = query_scores.get_score(query_id, doc_id)
        # 将余弦相似度分数与人工评分结合
        final_score = (score + average_score) / 2
        ranked_docs_with_scores.append((doc_id, final_score))
    ranked_docs_with_scores.sort(key=lambda x: x[1], reverse=True)
    return ranked_docs_with_scores[:limit]


# 主函数
def main():
    ######################################
    ##  1. 加载倒排索引文件
    stop_words = load_stop_words('stop_words.txt')
    index_file_path = 'inverted_index.pickle'
    document_store = read_docs()
    inverted_index = load_inverted_index(index_file_path)
    if inverted_index is None:
        inverted_index = build_and_save_inverted_index(document_store, index_file_path, stop_words)

    ######################################
    ##  2. 加载查询结果评分数据
    scors_file_path = 'query_scores.pickle'
    query_scores = load_scores(scors_file_path)  # 初始化查询评分数据

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
        document_vectors = build_document_vectors(words, inverted_index.index)

        # 3 计算文档与query的相关度 并据此排序文档
        ranked_docs_with_scores = rank_and_score_documents(query_vector, document_vectors, query_id, query_scores)
        
        # 4 打印查询结果及相关度
        for i, (doc_id, score) in enumerate(ranked_docs_with_scores):
            doc = document_store.get(doc_id, {})
            print(f"搜索结果: {i+1}\n题目: {doc_id}\n时间: {doc['Date']}, 相关度: {score:.4f}\nurl: {doc['URL']}\n主要内容: {doc['Description']}")
        # 5 为排序结果打分
        for doc_name, _ in ranked_docs_with_scores:
            try:
                score = float(input(f"请输入 {doc_name} 的相关性评分（0-10，输入'-1'跳过）："))
                if score == -1:  # 允许用户输入-1来跳过评分
                    continue
                query_scores.add_score(query_id, doc_name, score)
            except ValueError:
                print("输入无效，已跳过评分。")
        
        # 6 保存评分数据
        save_scores(query_scores, 'query_scores.pickle')
        print("评分数据已保存。")

if __name__ == "__main__":
    main()