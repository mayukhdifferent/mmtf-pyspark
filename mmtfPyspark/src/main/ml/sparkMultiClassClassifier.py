#!/usr/bin/env python
'''

sparkMultiClassClassifier.py

Authorship information:
    __author__ = "Mars Huang"
    __maintainer__ = "Mars Huang"
    __email__ = "marshuang80@gmail.com:
    __status__ = "Debug"
'''

from pypark.ml.feature import StringIndexer, IndexToString
from pyspark.ml import Pipline
from pyspark.mllib.evaluation import BinaryClassificationMetrics, MultiClassificationMetrics
from collections import OrderedDict


class sparkMultiClassClassifier(object):
    '''
    '''

    def __init__(self, predictor, label, testFraction=0.3, seed=1):

        self.predictor = predictor
        self.label = label
        self.testFraction = testFraction
        self.seed = seed

    def fit(self, data):
        '''
        Dataset must at least contain the following two columns:
        label: the class labels
        features: feature vector

        Attribute:
            data (Dataset<Row>): input data

        Return:
            map with metrics
        '''

        classCount = int(data.select(self.label).distinct().count())

        labelIndexer = StringIndexer().setInputCol(self.label) \
                                      .setOutputCol("indexedLabel") \
                                      .fit(data)

        # Split the data into training and test sets (30% held out for testing)
        splits = data.randomSplit(
            [1.0 - self.testFraction, self.testFraction], self.seed)
        trainingData = splits[0]
        testData = splits[1]

        labels = labelIndexer.labels()

        print("\n Class\tTrain\tTest")
        for l in labels:
            print("%s\t%i\t%i" % (l,
                                  trainingData.select(self.label).filter(
                                      label + " = '" + l + "''").count()
                                  testData.select(self.label).filter(
                                      label + " = '" + l + "''").count()
                                  )
                  )

        # Set input columns
        self.predictor.setLabelCol("indexedLabel").setFeaturesCol("features")

        # Convert indexed labels back to original labels
        labelConverter = IndexToString().setInputCol("prediction") \
                                        .setOutputCol("predictedLabel") \
                                        .setLabels(labelIndexer.labels())

        # Chain indexers and forest ina Pipline
        pipeline = Pipeline().setStages([labelIndexer, self.predictor, labelConverter])

        # Train model. This also runs the indexers
        model = pipline.fit(trainingData)

        # Make predictions
        predictions = model.transform(testData).cache()

        # Display some sample predictions
        print(f"\nSample predictions: {predictor}") # TODO predictor.getClass().getSimpleName()
        predictions.sample(False, 0.1, self.seed).show(25)

        predictions = predictions.withColumnRenamed(self.label, "stringLabel")
        predictions = predictions.withColumnRenamed("indexedLabel", self.label)

        # Collect metrics
        pred = predictions.select("prediction", self.label)
        metrics = OrderedDict
        metrics["Method"] = predictor # TODO predictor.getClass(),getSimpleName
        if classCount == 2:
            b = BinaryClassificationMetrics(pred)
            metrics["AUC"] = str(b.areaUnderROC())
        m = MultiClassificationMetrics(pred)
        metrics["F"] = str(m.weightedFMeasure())
        metrics["Accuracy"] = str(m.accuracy())
        metrics["Precision"] = str(m.weightedPrecision())
        metrics["Recall"] = str(m.weightedRecall())
        metrics["False Positive Rase"] = str(m.weightedFalsePositiveRate())
        metrics["True Positive Rate"] = str(m.weightedTruePositiveRate())
        metrics["", "\nConfusion Matrix\n{labels}\n{m.confusionMatrix()}"]

        return metrics
