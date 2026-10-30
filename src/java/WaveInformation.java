import java.nio.file.*;
import java.util.*;
import java.io.*;
import infodynamics.measures.continuous.kraskov.*;
import infodynamics.utils.EmpiricalMeasurementDistribution;

/** JIDT 1.6.1 runner. Input: headerless standardized, jittered Ho,Hn,Tp,Dx,Dy. */
public class WaveInformation {
  public static void main(String[] args) throws Exception {
    String input=args[0], output=args[1], measure=args[2];
    int k=Integer.parseInt(args[3]), window=Integer.parseInt(args[4]);
    int count=Integer.parseInt(args[5]), bins=Integer.parseInt(args[6]);
    long seed=Long.parseLong(args[7]);
    List<String> lines=Files.readAllLines(Path.of(input)); int n=lines.size();
    double[][] data=new double[n][5];
    for(int i=0;i<n;i++) { String[] fields=lines.get(i).split(","); for(int j=0;j<5;j++) data[i][j]=Double.parseDouble(fields[j]); }
    boolean mi=measure.equals("mi_height"), direction=measure.equals("cmi_direction");
    double[][] x=new double[n][direction?2:1], y=new double[n][1], z=new double[n][1];
    for(int i=0;i<n;i++) { x[i][0]=data[i][mi?0:direction?3:2]; if(direction) x[i][1]=data[i][4]; y[i][0]=data[i][1]; z[i][0]=data[i][0]; }
    double estimate; EmpiricalMeasurementDistribution dist=null;
    int[][] orders=new int[count][n]; Random random=new Random(seed);
    Integer[] ranked=new Integer[n]; for(int i=0;i<n;i++) ranked[i]=i;
    Arrays.sort(ranked, Comparator.comparingDouble(i -> data[i][0]));
    for(int b=0;b<count;b++) {
      for(int i=0;i<n;i++) orders[b][i]=i;
      if(bins==0) { for(int i=n-1;i>0;i--) {int j=random.nextInt(i+1), t=orders[b][i]; orders[b][i]=orders[b][j]; orders[b][j]=t;} }
      else for(int group=0;group<bins;group++) {
        int start=group*n/bins, stop=(group+1)*n/bins;
        for(int i=stop-1;i>start;i--) {int j=start+random.nextInt(i-start+1), a=ranked[i], c=ranked[j], t=orders[b][a]; orders[b][a]=orders[b][c]; orders[b][c]=t;}
      }
    }
    if(mi) {
      MutualInfoCalculatorMultiVariateKraskov1 c=new MutualInfoCalculatorMultiVariateKraskov1();
      c.setProperty("k", ""+k); c.setProperty("DYN_CORR_EXCL", ""+window); c.setProperty("NORMALISE","false"); c.setProperty("NOISE_LEVEL_TO_ADD","0"); c.setProperty("NUM_THREADS","4"); c.setProperty("USE_GPU","false"); c.setProperty("TIME_DIFF","0");
      c.initialise(1,1); c.setObservations(x,y); estimate=c.computeAverageLocalOfObservations();
      if(count>0) dist=c.computeSignificance(orders);
    } else {
      ConditionalMutualInfoCalculatorMultiVariateKraskov1 c=new ConditionalMutualInfoCalculatorMultiVariateKraskov1();
      c.setProperty("k", ""+k); c.setProperty("DYN_CORR_EXCL", ""+window); c.setProperty("NORMALISE","false"); c.setProperty("NOISE_LEVEL_TO_ADD","0"); c.setProperty("NUM_THREADS","4"); c.setProperty("USE_GPU","false");
      c.initialise(direction?2:1,1,1); c.setObservations(x,y,z); estimate=c.computeAverageLocalOfObservations();
      if(count>0) dist=c.computeSignificance(1,orders); // shuffle predictor, retain Hn and Ho
    }
    try(PrintWriter out=new PrintWriter(output)) {
      out.println("kind,index,nats,bits"); out.printf(Locale.ROOT,"observed,0,%.17g,%.17g%n",estimate,estimate/Math.log(2));
      if(dist!=null) for(int b=0;b<count;b++) out.printf(Locale.ROOT,"surrogate,%d,%.17g,%.17g%n",b,dist.distribution[b],dist.distribution[b]/Math.log(2));
    }
    System.out.printf(Locale.ROOT,"%s n=%d k=%d W=%d B=%d bins=%d bits=%.6f%n",measure,n,k,window,count,bins,estimate/Math.log(2));
  }
}
