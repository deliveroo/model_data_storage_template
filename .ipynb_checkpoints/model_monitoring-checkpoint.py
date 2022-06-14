import pandas as pd
import numpy as np
#regenerate identical synthetic data
np.random.seed(1234)
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pylab as plt
import ruptures as rpt


# Model Monitoring Utils
def generate_vlm_display(dfin, pdf_file, percentiles = [25,50,75]):
    df = dfin.copy()
    pdf_pages = PdfPages(pdf_file)
    nx,ny = np.shape(df)
    for i in range(ny):
        feature_name = df.columns[i]
        x = df.index
        y = df[feature_name].values
        
        # Create a figure instance (ie. a new page)
        fig = plt.figure(figsize=(8.27, 11.69), dpi=100)
        ax1 = fig.add_subplot(111)
        
        # Plot variable-level data
        y_percentiles = np.percentile(y, percentiles) 
        str_pc1 = ', '.join([str(int(pc))+'%' for pc in percentiles])+' percentiles'
        str_pc2 = ', '.join([str(np.round(pc,2)) for pc in y_percentiles])
        if i == 0:
            str_pc = str_pc1+'\n'+str_pc2
        else:
            str_pc = str_pc2
        label = feature_name+':\n'+ str_pc
        ax1.plot(x, y,label=label)
        ax1.set_ylabel('value')
        
        #show percentiles
        ax1.axhline(y_percentiles[0],ls=':',color='k')
        ax1.axhline(y_percentiles[1],ls='--',color='k')
        ax1.axhline(y_percentiles[2],ls=':',color='k')
        
        ax1.set_title(feature_name)
        ax1.legend()
        plt.grid()
    
        # Done with the page
        pdf_pages.savefig(fig)
    
    pdf_pages.close()


def calculate_change_points(dfin, percentiles= [25,50,75]):
    df = dfin.copy()
    nx,ny = np.shape(df)
    df_cp = pd.DataFrame({})
    for i in range(ny):
        feature_name = df.columns[i]
        x = df.index
        y = df[feature_name].values
        algo = rpt.Pelt(model="rbf").fit(y)
        result = algo.predict(pen=10)
        idxlo = 0
        for r in result:
            if r == nx:
                continue
            yn = y[idxlo:r]
            y_pc = np.percentile(yn,percentiles)
            idxlo = r
            dfn = pd.DataFrame({'feature_name':[feature_name],'datetime':[x[r]],'percentile':[percentiles],'value':[y_pc]})
            df_cp = pd.concat([df_cp, dfn])
            
    df_cp['datetime']=pd.to_datetime(df_cp['datetime']).dt.date
    df_cp = df_cp.set_index(['feature_name','datetime']).apply(pd.Series.explode).reset_index()
    return df_cp
    
    
    
if __name__ == '__main__':

    # Ingest model input features data pull (previous-1yr)
    #
    #
    #
    ## this is just a template so create some synthetic data here
    n_features = 7
    n_history = 365
    end_date = pd.Timestamp.today().date()
    start_date = end_date - pd.Timedelta(str(int(n_history-1))+'D')
    dates = pd.date_range(start_date, end_date, freq='1d')
    X = np.random.randn(n_history,n_features)
    ## inject artificial feature offsets
    offsets = 5*np.random.randn(n_features)
    X = X + offsets
    ## inject artifical trend
    idx_trend_feature = 4
    idx_trend_start = int(n_history/2)
    idx_trend_end = int(3/4*n_history)
    trend = 0.1*(np.arange(n_history) - idx_trend_start) + X[idx_trend_start,idx_trend_feature]
    trend[:idx_trend_start]=0
    trend[idx_trend_end:]=trend[idx_trend_end]
    X[:, idx_trend_feature] += trend 
    df = pd.DataFrame(X,columns = ['feature_'+str(i) for i in range(n_features)])
    df.index = dates
    
    
    
    
    
    ## Change-point detection
    df_cp = calculate_change_points(df, percentiles= [25,50,75])
    
    
    ## Monitoring Output
    pdf_file = './img/variable_level_monitoring.pdf'
    generate_vlm_display(df, pdf_file, percentiles = [25,50,75])
    
    
    
    
    
    
    