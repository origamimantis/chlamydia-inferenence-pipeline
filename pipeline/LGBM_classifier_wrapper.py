
class LGBM_Classifier_wrapper:
    def __init__(self, params=None, num_rounds=None, class_mapping=None, early_stopping_rounds=0):
        
        if not params:
            # Booster parameters:
            self.params = {
                'num_leaves': 50, 
                'num_iterations':100,
                'objective': 'multiclass',
                'num_class':2,
                "num_threads": 16,
                'metric': 'multi_logloss',
                'boosting':'goss',
                "early_stopping_rounds":early_stopping_rounds,
                'verbose': -1
            }
        else:
            self.params =params
        
        if not class_mapping or not isinstance(mapping, dict):
            raise ValueError('class mapping must be provided by using a dict. non numeric class labels ->> to integers')
        
        self._class_mapping = class_mapping
        
        if num_rounds:
            self._params['num_iterations']= num_rounds
    
    def train(self, train_data, eval_data):
        self.model = lgb.train(params=self._params, train_set=train_data, valid_sets=eval_data)
    
    
    def predict(self, test_data):
        PRED_FEATURE_LIST = ['solidity', 'extent', 'sphericity', 'axial_ratio']

        ypred = self.model.predict(test_data)
        return ypred
    
    def get_class_mapping(self):
        return self._class_mapping
        
    def save(self, path):
        import pickle
        
        if not self.model:
            raise Exception('No training odne yet or model found')
            
        x = LGBM_Classifier_wrapper(params=self._params,class_mapping=self._class_mapping)
        x.model = self.model
        
        with open(path, 'wb') as f:
            pickle.dump(x, f)
        del x
    
    def __repr__(self):
        
        return f"""
        
        LightGBM serialized model with additional metadata
        
        Class mappings = {self.class_mapping}
        
        LGBM model params = {self.params} """
    