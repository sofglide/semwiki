FROM tensorflow/serving

ENV MODEL_BASE_PATH="/models"
ENV MODEL_NAME="USE_3"

COPY universal-sentence-encoder-multilingual_3.tar.gz $MODEL_BASE_PATH/$MODEL_NAME/1/universal-sentence-encoder-multilingual_3.tar.gz
RUN cd $MODEL_BASE_PATH/$MODEL_NAME/1; tar -zxf universal-sentence-encoder-multilingual_3.tar.gz

EXPOSE 8501

# curl GET http://172.17.0.2:8501/v1/models/USE_3
# curl -XPOST -d '{"instances": ["toto"]}' http://172.17.0.2:8501/v1/models/USE_3:predict

# curl -XPOST -d '{"instances": ["toto", "tata"]}' http://3.248.253.135:8501/v1/models/USE_3:predict | jq
# curl -u semwiki:SemWiki21! https://search-semwiki-6yrq325yksanyp2gwbjbk63une.eu-west-1.es.amazonaws.com